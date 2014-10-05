#include<stdio.h>
#include<stdlib.h>

void exchange(int*, int*);
int position(int [], int, int);

/*exchange two variables*/
void exchange(int* a, int* b){
    int tmp;
    tmp = *a;
    *a = *b;
    *b = tmp;
}

/*a[] begin p, last r*/
int position(int a[], int p, int r){
    int q = r;
    int i=-1;
    int j=0;
    int tmp=0;
    for(;j<r;){
        tmp = a[i+1];
        if(a[j]<a[r]){
            exchange(&a[j++],&a[(i++)+1]);
        }else{
            j++;
        }
    }
    /*step 1*/
    exchange(&a[i+1], &a[r]);
    return i+1;
}

/*quick sort*/
int quick_sort_qy(int a[], int l, int r){
    /*step 3*/
    if(l>=r)
        return 0;
    int pos = position(a, l, r);
    /*step 2*/
    quick_sort_qy(a, l, pos-1);
    quick_sort_qy(a, pos+1, r);
}

int main(){
    int a[] = {2,5,1,67,31};

    quick_sort_qy(a, 0, 4);

    for(int i=0;i<sizeof(a)/sizeof(a[0]);i++){
        printf("%d\t", a[i]);
    }
    printf("\n");
    return 0;
}
