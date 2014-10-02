#include<iostream>

int main(){
    const int size_n = 3;
    int a[size_n]={12,3,1};

    for(int i=1;i<size_n;i++){
        int key=a[i];
        int j=i-1;
        while((j>=0)&&(key<a[j])){
            a[j+1] = a[j];
            j--; 
        }
        a[j+1]=key;
    }

    for(int i=0;i<size_n;i++){
        std::cout<<a[i]<<std::endl;
    }

    return 0;
}
