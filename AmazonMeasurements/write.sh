#!/bin/sh
echo "Writing"

function run_test {
	n=$(($3+$4+$5))
	echo "---===  $1 $2 k=$3 r=$4 z=$5 rand=$6 n=$n servers=$7 ===---"
	python parallel_platform.py $1 $2 $3 $4 $5 $6 $7 $n
}

function basic_read_test {
	run_test read $1 $2 $3 $4 NONE $5
	run_test fread $1 $2 $3 $4 NONE $5
	run_test sf1 $1 $2 $3 $4 NONE $5
	if (($3>1)); then
		run_test sf2 $1 $2 $3 $4 NONE $5
	fi
}

function rand_read_test {
	racod=$1"_RA"
	run_test rcr $racod $2 $3 $4 NONE $5 $n
}

function read_test {
	basic_read_test $1 $2 $3 $4 $5
	rand_read_test $1 $2 $3 $4 $5
}

function run_codecs {
	servers=$2
	k=$1
	echo "---=== RUNNING TEST FOR K=$k SN=$servers ===---"
	for re in 2
	do
		for z in 2
	  		do
	    		for cod in PSS BB
	    		do
					for rand in AES
					do
	      				run_test write $cod $k $re $z $rand $servers $n
	    			done
					read_test $cod $k $re $z $servers
	  			done
		done
		
		z=0
		rand=NONE
		for cod in AES CHA AONT_AES NONE
		do
			run_test write $cod $k $re $z $rand $servers $n
			read_test $cod $k $re $z $servers
		done
	done
}

function run_sss {
	servers=7
	k=1
	cod=SSS
	echo "---=== RUNNING SSS TEST FOR K=$k SN=$servers ===---"
	for z in 2
	do
		for re in 2
		do 
			for rand in AES
			do
				run_test write $cod $k $re $z $rand $servers $n
			done
			basic_read_test $cod $k $re $z $servers
		done
	done
}


cp ../client/config37.xml ../client/config.xml
python prepare_client.py
run_codecs 32 37
python start_machines.py stop machines37to13.txt

cp ../client/config13.xml ../client/config.xml
python prepare_client.py
run_codecs 8 13
python start_machines.py stop machines37to7.txt

cp ../client/config7.xml ../client/config.xml
python prepare_client.py
run_codecs 2 7 
run_sss
python start_machines.py stop machines37.txt
