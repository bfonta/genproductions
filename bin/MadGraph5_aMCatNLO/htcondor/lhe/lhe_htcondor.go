
package main

import (
	"fmt"
	"os"
	"flag"
	// "strconv"
	"strings"
	"regexp"
	fp "path/filepath"
)

func check(e error) {
    if e != nil {
        panic(e)
    }
}

func contains(s []string, e string) bool {
    for _, a := range s {
        if a == e {
            return true
        }
    }
    return false
}

func main() {
	modeFlag := flag.String("mode", "", "Input directory, where the tarballs are stored.")
	tagFlag := flag.String("tag", "", "Tag, used for input cards and job names.")
	flag.Usage = func() {
	    fmt.Fprintf(os.Stderr, "Usage: go run lhe_htcondor.go -mode=XXX -tag=ManualV2\n")
	}   
	flag.Parse()
	if *modeFlag == "" || *tagFlag == "" {
		fmt.Println("Please specify the '-mode=...' and the '-tag=...' options.")
		os.Exit(1)
	}
	modes := [3]string{"all", "resonly", "nores"}
	if ! contains(modes[:], *modeFlag) {
		fmt.Println(fmt.Sprintf("Option %s is not supported for `mode`!", *modeFlag))
		os.Exit(1)
	}
	
	indir := fp.Join("/eos/user/b/bfontana/FiniteWidth/", *tagFlag + "_" + *modeFlag)
	base_dir := fp.Join("/afs/cern.ch/work/",
		string(os.Getenv("USER")[0]), os.Getenv("USER"),
		"genproductions/bin/MadGraph5_aMCatNLO/")
	condor_dir := fp.Join(base_dir, "htcondor/lhe/")
	condor_out := fp.Join(condor_dir, fmt.Sprintf("out_%s/", *modeFlag)) + "/"

	outfile := *modeFlag + "_M$(Mass)_ST$(Stheta)_L$(Lambda)_K$(Kappa)"

	// masses  := [8]string{"280.00",  "280.00",  "280.00",  "280.00",  "500.00",   "500.00",  "500.00", "500.00"}
	// sthetas := [8]string{"0.14",    "0.29",    "0.29",    "0.14",    "0.27",     "0.62",    "0.62",   "0.27"}
	// lambdas := [8]string{"463.05",  "456.08",  "-456.29", "-462.96", "-540.97",  "-15.72", "15.73",   "539.06"}
	// kappas  := [8]string{"1.00",    "1.00",    "1.00",    "1.00",    "1.00",     "1.00",    "1.00",   "1.00"}
	masses  := [2]string{"500.00",  "500.00"}
	sthetas := [2]string{"0.03",   "0.03"} // the datacards actually used 0.033
	lambdas := [2]string{"-600.00", "600.00",}
	kappas  := [2]string{"1.00",    "1.00"}

	loop_inside := ""
	r1 := regexp.MustCompile(regexp.QuoteMeta("."))
	r2 := regexp.MustCompile(regexp.QuoteMeta("-"))
	zipdirs := [2]string{condor_dir, condor_out}
	for _, d := range zipdirs {
		_, err := os.Stat(d)
		if os.IsNotExist(err) {
			fmt.Println(fmt.Sprintf("Folder %s already exists!", d))
			fmt.Println(fmt.Sprintf("Deletion command: rm -r %s", d))
			os.Exit(1)
		}
		os.Mkdir(d, os.ModeDir)
	}

	for i := range masses {
		mstr := r1.ReplaceAllString(masses[i], "p")
		mstr = r2.ReplaceAllString(mstr, "m")
		sstr := r1.ReplaceAllString(sthetas[i], "p")
		sstr = r2.ReplaceAllString(sstr, "m")
		lstr := r1.ReplaceAllString(lambdas[i], "p")
		lstr = r2.ReplaceAllString(lstr, "m")
		kstr := r1.ReplaceAllString(kappas[i], "p")
		kstr = r2.ReplaceAllString(kstr, "m")
		loop_inside += "    " + mstr + ", " + sstr + ", " + lstr + ", " + kstr
		if !(masses[i] == masses[len(masses)-1]   && sthetas[i] == sthetas[len(sthetas)-1] &&
			lambdas[i] == lambdas[len(lambdas)-1] && kappas[i] == kappas[len(kappas)-1]) {
			loop_inside += "\n"
		}
	}

	nevents := "100000" // "5000"
	m := []string{
		"universe = vanilla",
		"executable = " + fp.Join(condor_dir, "lhe_htcondor.sh"),
		fmt.Sprintf("arguments  = $(Mass) $(Stheta) $(Lambda) $(Kappa) %s %s %s %s",
			*modeFlag, indir, nevents, *tagFlag),
		"output     = " + condor_out + outfile + ".out",
		"error      = " + condor_out + outfile + ".err",
		"log        = " + condor_out + outfile + ".log",
		
		"getenv = true",
		fmt.Sprintf("+JobBatchName=\"FW_LHE_%s\"", *modeFlag),
		"+JobFlavour = \"workday\"", // 8 hours (see https://batchdocs.web.cern.ch/local/submit.html)
		"RequestCpus = 1",
		
		"queue Mass, Stheta, Lambda, Kappa from (",
		loop_inside,
		")"}
	
	f, err := os.Create(fp.Join(condor_dir, "lhe_htcondor_" + *modeFlag + ".condor"))
	check(err)
	defer f.Close()
	f.WriteString(strings.Join(m, "\n"))
}
