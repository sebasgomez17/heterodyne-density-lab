#include "hdl_core.h"
#include <math.h>
#define HDL_PI 3.14159265358979323846264338327950288

int hdl_abel_density(size_t nx, const double *x, double R, double n0,
                     double nbase, double ln, double na, int nq, double *out) {
    size_t i; int k;
    if (!(R>0) || !(ln>0) || !(na>0) || nq<2) return 1;
    for (i=0;i<nx;++i) {
        double a=fabs(x[i]), smax, sum=0.0;
        if (!isfinite(a)) return 1;
        if (a>=R) {out[i]=0.0; continue;}
        smax=sqrt(fmax(0.0,R*R-a*a));
        for (k=0;k<nq;++k) {
            double s=smax*(double)k/(double)(nq-1);
            double rr=a*a+s*s;
            double exponent = (na==2.0) ? rr/(2.0*ln*ln)
                : pow(sqrt(rr)/ln,na)/na;
            double value=(n0-nbase)*exp(-exponent)+nbase;
            sum += (k==0 || k==nq-1) ? 0.5*value : value;
        }
        out[i]=2.0*smax*sum/(double)(nq-1);
    }
    return 0;
}

int hdl_abel_basis(size_t nx, const double *x, double R, int max_order,
                   int nq, double *out) {
    size_t i; int k,n;
    if (!(R>0) || max_order<0 || nq<2) return 1;
    for (i=0;i<nx;++i) {
        double a=fabs(x[i]), smax;
        double *row=out+i*(size_t)(max_order+1);
        if (!isfinite(a)) return 1;
        for(n=0;n<=max_order;++n) row[n]=0.0;
        if(a>=R) continue;
        smax=sqrt(fmax(0.0,R*R-a*a));
        row[0]=2.0*smax; /* constant basis integrates exactly */
        for(k=0;k<nq;++k) {
            double s=smax*(double)k/(double)(nq-1);
            double angle=HDL_PI*sqrt(a*a+s*s)/R;
            double c=cos(angle), previous=1.0, current=c;
            double w=(k==0 || k==nq-1) ? 0.5 : 1.0;
            for(n=1;n<=max_order;++n) {
                double next;
                row[n] += w*(1.0-((n%2) ? -current : current));
                next=2.0*c*current-previous;
                previous=current; current=next;
            }
        }
        for(n=1;n<=max_order;++n) row[n]*=2.0*smax/(double)(nq-1);
    }
    return 0;
}

int hdl_phasor(size_t ne, size_t q, const double *h, const double *weights,
               double factor, double *re, double *im, double *linear) {
    size_t j,k;
    if(q==0 || !(factor>0)) return 1;
    for(j=0;j<ne;++j) {
        double zr=0.0,zi=0.0,hl=0.0;
        for(k=0;k<q;++k) {
            size_t at=j*q+k; double phi=-factor*h[at],w=weights[at];
            zr+=w*cos(phi); zi+=w*sin(phi); hl+=w*h[at];
        }
        re[j]=zr; im[j]=zi; linear[j]=hl;
    }
    return 0;
}

int hdl_iq_samples(size_t ne, size_t nmc, const double *re,
                   const double *im, const double *sigma,
                   const double *normals, double factor,
                   double *I, double *Q, double *phase, double *density) {
    size_t m,j;
    if(ne==0 || nmc==0 || !(factor>0)) return 1;
    for(m=0;m<nmc;++m) for(j=0;j<ne;++j) {
        size_t at=m*ne+j;
        I[at]=re[j]+sigma[j]*normals[(2*m)*ne+j];
        Q[at]=im[j]+sigma[j]*normals[(2*m+1)*ne+j];
        phase[at]=atan2(Q[at],I[at]); density[at]=-phase[at]/factor;
    }
    return 0;
}
