"""Even penalized cubic B-spline, with cached linear operators and batched GCV.

This implements the MATLAB toolbox-independent algorithm: multiplicity weights,
second coefficient differences, 1e-12 ridge, and per-realization GCV selection.
"""
import numpy as np
from scipy.interpolate import BSpline

class SplineOperator:
    def __init__(self,x_signed,radius,options,r_eval):
        x=np.asarray(x_signed,dtype=float)
        if not np.isfinite(x).all() or (np.abs(x)>radius*(1+1e-12)).any():raise ValueError('Spline support must be finite and inside the plasma')
        u=np.round((np.abs(x)/radius)**2,12)
        self.u,self.group=np.unique(u,return_inverse=True)
        count=np.bincount(self.group).astype(float)
        if self.u.size<4:raise ValueError('At least four unique spline support radii are required')
        n=max(4,min(options.basis_count,self.u.size));degree=3
        internal=np.arange(1,n-degree)/(n-degree)
        self.knots=np.r_[np.zeros(4),internal,np.ones(4)]
        B=BSpline.design_matrix(self.u,self.knots,degree).toarray()
        self.evaluation=BSpline.design_matrix(np.clip((np.asarray(r_eval)/radius)**2,0,1),self.knots,degree).toarray()
        # Explicit grouping matrix, reusable for every realization.
        self.merge=np.zeros((self.u.size,x.size))
        self.merge[self.group,np.arange(x.size)]=1/count[self.group]
        self.sqrt_counts=np.sqrt(count)
        self.Bw=B*self.sqrt_counts[:,None]
        normal=self.Bw.T@self.Bw
        D=np.diff(np.eye(n),n=2,axis=0)
        self.lambdas=np.asarray(options.lambda_candidates if options.lambda_value is None else [options.lambda_value],dtype=float)
        matrices=normal[None,:,:]+self.lambdas[:,None,None]*(D.T@D)[None,:,:]+1e-12*np.eye(n)[None,:,:]
        self.solvers=np.linalg.solve(matrices,np.broadcast_to(self.Bw.T,(len(self.lambdas),n,self.u.size)))
        self.hat=np.einsum('ub,lbc->luc',self.Bw,self.solvers)
        dof=np.trace(self.hat,axis1=1,axis2=2)
        self.denominator=np.maximum(1-dof/self.u.size,np.sqrt(np.finfo(float).eps))**2
        self.clip_nonnegative=options.clip_nonnegative

    def apply(self,y):
        """Input (realizations,support); return (realizations,r_grid), lambdas."""
        y=np.asarray(y,dtype=float)
        if y.ndim!=2 or y.shape[1]!=self.merge.shape[1] or not np.isfinite(y).all():raise ValueError('Invalid spline sample matrix')
        grouped=y@self.merge.T
        yw=grouped*self.sqrt_counts
        # Scale before GCV/solve as in MATLAB to protect large SI density values.
        scale=np.max(np.abs(yw),axis=1);scale[scale==0]=1.0
        normalized=yw/scale[:,None]
        if len(self.lambdas)==1:
            selected=np.zeros(len(y),dtype=int)
        else:
            predicted=np.einsum('luc,mc->lmu',self.hat,normalized,optimize=True)
            residual=predicted-normalized[None,:,:]
            gcv=np.mean(residual**2,axis=2)/self.denominator[:,None]
            selected=np.argmin(gcv,axis=0)
        coeff=np.einsum('mbu,mu->mb',self.solvers[selected],normalized)*scale[:,None]
        values=coeff@self.evaluation.T
        if self.clip_nonnegative:values=np.maximum(values,0)
        return values,self.lambdas[selected]
