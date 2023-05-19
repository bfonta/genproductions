
package main

import (
	"fmt"
	"os"
	"flag"
	// "strconv"
	"strings"
	"regexp"
	"errors"
	fp "path/filepath"
)

func check(e error) {
    if e != nil {
        panic(e)
    }
}

func main() {
        outdirFlag := flag.String("outdir", "", "Output directory.")
	tagFlag  := flag.String("tag", "", "Input directory, where the tarballs are stored.")
	flag.Usage = func() {
	    fmt.Fprintf(os.Stderr, "Usage: go run lhe_htcondor.go -outdir=LHE_Out -tag=MyTag\n")
	}   
	flag.Parse()
	if *outdirFlag == "" {
		fmt.Println("Plase specify the '-outdir=...' option.")
		os.Exit(1)
	}
	if *tagFlag == "" {
		fmt.Println("Plase specify the '-tag=...' option.")
		os.Exit(1)
	}
	
	base_dir := fp.Join("/afs/cern.ch/work/",
		string(os.Getenv("USER")[0]), os.Getenv("USER"),
		"genproductions/bin/MadGraph5_aMCatNLO/")
	condor_dir := fp.Join(base_dir, "htcondor/")
	condor_out := fp.Join(condor_dir, fmt.Sprintf("out_lhe_%s/", *outdirFlag)) + "/"
	out_dir := fp.Join(base_dir, *outdirFlag)

	outfile := "ST$(Stheta)_K$(Kappa)_M$(Mass)"

	// widths := [...]string{"narrow"} // "10pcts", "20pcts", "30pcts")
	// masses := [25]string{"250", "260", "270", "280", "300", "320", "350", "400",
	// 	"450", "500", "550", "600", "650", "700", "750", "800",
	// 	"850", "900", "1000", "1250", "1500", "1750", "2000", "2500", "3000"}
	masses  := [1]string{"250"}
	sthetas := [3]string{"0.2", "0.5", "0.8"}
	kappas  := [3]string{"1.0", "2.0", "3.0"}

	loop_inside := ""
	r := regexp.MustCompile(regexp.QuoteMeta("."))
	zipdirs := [2]string{out_dir, condor_out}
	for _, d := range zipdirs {
		if _, err := os.Stat(d); errors.Is(err, os.ErrNotExist) {
			os.Mkdir(d, os.ModeDir)
		} else {
			fmt.Println(fmt.Sprintf("Folder %s already exists!", d))
			fmt.Println(fmt.Sprintf("Deletion command: rm -r %s", d))
			os.Exit(1)
		}
	}

	for _, st := range sthetas {
		ststr := r.ReplaceAllString(st, "p")
		for _, kap := range kappas {
			kstr := r.ReplaceAllString(kap, "p")
			for _, m := range masses {
				loop_inside += "    " + m + ", " + ststr + ", " + kstr
				if !(m==masses[len(masses)-1] && st==sthetas[len(sthetas)-1] && kap==kappas[len(kappas)-1]) {
					loop_inside += "\n"
				}
			}
		}
	}

	nevents := "10"
	m := []string{
		"universe = vanilla",
		"executable = " + fp.Join(condor_dir, "lhe_htcondor.sh"),
		fmt.Sprintf("arguments  = $(Mass) $(Stheta) $(Kappa) %s %s %s", fp.Join(base_dir, *outdirFlag), fp.Join(base_dir, *tagFlag), nevents),
		"output     = " + condor_out + outfile + ".out",
		"error      = " + condor_out + outfile + ".err",
		"log        = " + condor_out + outfile + ".log",
		
		"getenv = true",
		fmt.Sprintf("+JobBatchName=\"FW_LHE_%s\"", *outdirFlag),
		"+JobFlavour = \"longlunch\"", // 2 hours (see https://batchdocs.web.cern.ch/local/submit.html)
		"RequestCpus = 1",
		
		"queue Mass, Stheta, Kappa from (",
		loop_inside,
		")"}
	
	f, err := os.Create(fp.Join(condor_dir, "lhe_htcondor_" + *outdirFlag + ".condor"))
	check(err)
	defer f.Close()
	f.WriteString(strings.Join(m, "\n"))
}
