/*论寻算法头文件*/

#ifndef C_DROPBOX
#define C_DROPBOX

typedef struct{
    char name;
    int weight;
    int effective_weight;
    int current_weight;
}peer_t ;

//typedef struct peer_s peer_t;

peer_t*
round_robin_get_peer(peer_t* peers[], int n);

#endif


/*论寻算法实现文件*/
#include<stdio.h>
#include"round_robin.h"

peer_t*
round_robin_get_peer(peer_t* peers[], int n){
    
    peer_t* best=peers[0];
    int total_weight=0;
    int i;

    for(i=0;i<n;i++){
        peers[i]->current_weight += peers[i]->effective_weight;
        total_weight+=peers[i]->effective_weight;

        if(peers[i]->effective_weight<peers[i]->weight){
            peers[i]->effective_weight++;
        }
        if(best->current_weight<peers[i]->current_weight)
            best = peers[i];
    }

    best->current_weight-=total_weight;
    printf("choose:%c, a:%d, b:%d, c:%d\n", best->name, peers[0]->current_weight, peers[1]->current_weight, peers[2]->current_weight);
    return best;
}


/*main入口*/
#include<stdio.h>
#include"round_robin.h"

int main(){
    peer_t a={'a',5,0,5};
    peer_t b={'b',1,0,1};
    peer_t c={'c',1,0,1};

    peer_t* peers[3]={&a,&b,&c};

    peer_t* ret_peer;

    int i;

    for(i=0;i<10;i++){
        ret_peer = round_robin_get_peer(peers, 3);
        //printf("%c\t", ret_peer->name);
    }

    printf("\ndone\n");

    return 0;
}
