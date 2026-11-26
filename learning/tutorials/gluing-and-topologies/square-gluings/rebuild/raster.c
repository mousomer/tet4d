#include <math.h>
#include <stdlib.h>
typedef struct {float z,r,g,b,k; int next;} Hit;
#include <stdint.h>
void paint(uint8_t *im,int W,int H,const double *xy,const double *rgb,const double *alpha,const int *order,int count){
int cap=W*H,used=0;Hit *hits=malloc(cap*sizeof(Hit));int *heads=calloc(W*H,sizeof(int));
for(int j=0;j<count;j++){int f=order[j];const double *q=xy+9*f,*c=rgb+9*f;double x=q[0],y=q[1],u=q[3]-x,v=q[4]-y,s=q[6]-x,t=q[7]-y,D=u*t-v*s;
if(fabs(D)<1e-10)continue;
for(int iy=fmax(0,floor(fmin(y,fmin(q[4],q[7]))));iy<=fmin(H-1,ceil(fmax(y,fmax(q[4],q[7]))));iy++){
for(int ix=fmax(0,floor(fmin(x,fmin(q[3],q[6]))));ix<=fmin(W-1,ceil(fmax(x,fmax(q[3],q[6]))));ix++){
double dx=ix+.501-x,dy=iy+.503-y,b=(dx*t-dy*s)/D,g=(u*dy-v*dx)/D,a=1-b-g;if(a<0||b<0||g<0)continue;
int i=W*iy+ix;if(++used>=cap){cap*=2;hits=realloc(hits,cap*sizeof(Hit));}
Hit h={a*q[2]+b*q[5]+g*q[8],a*c[0]+b*c[3]+g*c[6],a*c[1]+b*c[4]+g*c[7],a*c[2]+b*c[5]+g*c[8],alpha[f],0};
int *slot=&heads[i];while(*slot && hits[*slot].z<h.z)slot=&hits[*slot].next;
h.next=*slot;hits[used]=h;*slot=used;
}}}
for(int i=0;i<W*H;i++){float r=im[3*i],g=im[3*i+1],b=im[3*i+2];
for(int id=heads[i];id;id=hits[id].next){Hit h=hits[id];r+=(h.r-r)*h.k;g+=(h.g-g)*h.k;b+=(h.b-b)*h.k;}
im[3*i]=r; im[3*i+1]=g; im[3*i+2]=b;}free(heads);free(hits);}
