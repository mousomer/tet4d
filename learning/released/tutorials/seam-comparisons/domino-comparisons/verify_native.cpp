#include "tet4d_core/explorer_piece.hpp"
#include <iostream>
#include <stdexcept>
using namespace tet4d::core;
int main(int argc, char** argv) {
    for (int arg=1; arg<argc; ++arg) for (int g=0; g<3; ++g) {
        ExplorerPiece p;
        p.object_namespace="00000000000000000000000000000001";
        p.object_ordinal=1;
        p.profile={1,2,{5,5},{}};
        if (g==1) p.profile.seams={{"x",{0,"-"},{0,"+"},{{0},{-1}},true},{"y",{1,"-"},{1,"+"},{{0},{-1}},true}};
        else p.profile.seams={{"a",{0,"-"},{1,"-"},{{0},{g==0?1:-1}},true},{"b",{0,"+"},{1,"+"},{{0},{1}},true}};
        for (int i=0;i<2;++i) {
            p.rest_cells.push_back({i,{{i,0}}});
            p.cells.push_back({i,0,{{i,1}},{}});
        }
        int rev=0;
        for(char c:std::string(argv[arg])) {
            auto act = MoveStepQuery{(c=='L'||c=='R')?0:1,(c=='L'||c=='D')?-1:1};
            auto r=c=='T'?propose_piece_rotation(p,rev,1):propose_piece_translation(p,rev,act);
            if(!r.candidate) throw std::runtime_error(piece_failure_name(r.failure));
            p=r.candidate->target;
            std::cout<<argv[arg]<<" "<<g<<" "<<++rev;
            for(auto &cell:p.cells) for(auto x:cell.coordinate.values) std::cout<<" "<<x;
            bool touches=false;
            for(int a=0;a<2;++a) for(int s:{-1,1}) {
                PieceCell other; PieceWitness w;
                if(step_explorer_cell(p,p.cells[0],{a,s},other,w)!=PieceFailure::none) return 2;
                touches |= other.coordinate==p.cells[1].coordinate;
            }
            std::cout<<" "<<touches<<"\n";
        }
    }
}
