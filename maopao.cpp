//冒泡
#include<iostream>

void maopao(int* a, int n){
    for(int i=0;i<n;i++){
        for(int j=1;j<n-i;j++){
            if(a[j-1]>a[j]){
                int t = a[j];
                a[j]=a[j-1];
                a[j-1]=t;
            }
        }
    }
}

int main(){
    int a[5] = {13,43,21,6,21};
    maopao(a,5);
    for(int i = 0;i<5;i++){
        std::cout<<a[i]<<std::endl;
    }
    return 0;
}
