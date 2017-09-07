#!/bin/sh
echo "Writing"

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
					for rand in AES NONE
					do
	      				n=$(($k+$re+$z))
	      				echo "---=== WRITE $cod $rand k=$k r=$re z=$z n=$n sn=$servers ===---"
	      				python parallel_platform.py write $cod $k $re $z $rand $servers $n
	    			done
	    			echo "---=== READ $cod $rand k=$k r=$re z=$z n=$n sn=$servers ===---"
					python parallel_platform.py read $cod $k $re $z NONE $servers $n
					echo "---=== FAST_READ $cod $rand k=$k r=$re z=$z n=$n sn=$servers ===---"
					python parallel_platform.py fread $cod $k $re $z NONE $servers $n
					cod+="_RA"
					echo "---=== RANDOM CHUNK READ $cod $rand k=$k r=$re z=$z n=$n sn=$servers ===---"
					python parallel_platform.py rcr $cod $k $re $z NONE $servers $n
	  			done
		done
		
		z=0
		n=$(($k+$re))
		for cod in AES CHA AES_BC AONT_AES AONT_CHA AONT_AES_BC NONE
		do
			echo "---===  WRITE $cod k=$k r=$re n=$n sn=$servers ===---"
			python parallel_platform.py write $cod $k $re 0 NONE $servers $n
			echo "---=== READ $cod k=$k r=$re z=$z n=$n sn=$servers ===---"
			python parallel_platform.py read $cod $k $re 0 NONE $servers $n
			echo "---=== FAST_READ $cod k=$k r=$re z=$z n=$n sn=$servers ===---"
			python parallel_platform.py fread $cod $k $re 0 NONE $servers $n
			cod+="_RA"
			echo "---=== RANDOM CHUNK READ $cod k=$k r=$re z=$z n=$n sn=$servers ===---"
			python parallel_platform.py rcr $cod $k $re 0 NONE $servers $n
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
			for rand in AES SIMPLE NONE
			do
				n=$(($z+$re+$k))
		  		echo "---===  SSS $rand r=$re z=$z sn=$servers ===---"
	  			python parallel_platform.py write $cod $k $re $z $rand $servers $n
			done
			echo "---=== READ $cod $rand k=$k r=$re z=$z n=$n sn=$servers ===---"
	  		python parallel_platform.py read $cod $k $re $z NONE $servers $n
	  		echo "---=== FAST READ $cod $rand k=$k r=$re z=$z n=$n sn=$servers ===---"
			python parallel_platform.py fread $cod $k $re $z NONE $servers $n
			cod+="_RA"
			echo "---=== RANDOM CHUNK READ $cod $rand k=$k r=$re z=$z n=$n sn=$servers ===---"
			python parallel_platform.py rcr $cod $k $re $z NONE $servers $n
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
