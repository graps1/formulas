import os
import re
from typing import Union
from .formula import Formula
from .utils import cnf2dimacs

class GPMC:
    def __init__(self, 
        src = "/usr/local/bin/gpmc", 
        tmp_filename = "/tmp/dimacs.cnf",
        bj=True, cs=3500):
        self.__solver_dir = "/".join(src.split("/")[:-1])
        self.__solver_name = src.split("/")[-1]
        self.__tmp_filename = tmp_filename
        self.__bj = bj
        self.__cs = cs 

    def satcount_file(self, cnf_file, debug=False):
        cnf_file_abs = os.path.abspath(cnf_file)
        file_content = open(cnf_file, "r").read().split("\n")
        mode = "2" if "c t pmc" in file_content else "0"
        command =  f'''
            cd {self.__solver_dir} && 
            {self.__solver_dir}/{self.__solver_name} {'-bj' if self.__bj else '-no-bj'} -cs={self.__cs} -mode={mode} {cnf_file_abs}
        '''
        ret = os.popen(command).read()
        if debug: print(ret)
        satcount = int(float(re.findall(r"c s exact arb int (.*)", ret)[0]))
        return satcount 

    def satcount(self, cnf: Union[Formula, list[list[int]]], debug=False, ex_quantified=set()):
        if isinstance(cnf, Formula):
            cnf, var2idx = cnf.tseitin()
            ex_quantified = { var2idx[p] for p in (set(var2idx.keys()) - cnf.vars) | ex_quantified }
        with open(self.__tmp_filename, "w") as fw:
            nr_vars = max(max(abs(lit) for lit in cl) for cl in cnf)
            all_vars = set(range(1, nr_vars+1))
            dimacs = cnf2dimacs(cnf, projected=all_vars-ex_quantified)
            fw.write(dimacs)
        value = self.satcount_file(self.__tmp_filename, debug=debug)
        os.remove(self.__tmp_filename)
        return value


if __name__ == "__main__":
    f = Formula.parse("~x1 & (x2 | x3)") & Formula.parse("~x4")
    gpmc = GPMC()
    ex_quantified={"x2", "x3"}
    result_tseitin = gpmc.satcount(f, debug=False, ex_quantified=ex_quantified)
    result_hand_coded = gpmc.satcount([[-1], [2,3], [-4]], debug=False, ex_quantified={2,3})
    print(f"analyzing f={f}")
    print(f"existentially quantified={ex_quantified}")
    print(f"satcount via tseitin transformation: {result_tseitin}")
    print(f"satcount of hand-coded cnf: {result_hand_coded}")
    print(f"variables in f: {f.vars}")
    print(f"cofactor wrt x2 = 1: {f.cofactor('x2', True)}")
 