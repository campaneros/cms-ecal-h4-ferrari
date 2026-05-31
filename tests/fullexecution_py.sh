#!/bin/bash


# --- launch settings with beam|laser as input parameter ---
if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <run_number> <spill_number> <beam|laser|beam+laser> [noplots] [nounpack]"
    exit 1
fi
RUN=$1
SPILL=$(printf "%04d" $((10#$2)))
SPILL_NO=$((10#$SPILL))
mode=$3

if [ "$4" == "noplots" ]; then
  doplots="0"
else
  doplots="1"
fi

nounpack=$5

if [ "$mode" == "laser" ]; then
    option="laser"
elif [[ "$mode" == *"+laser" ]]; then
    # extract the part before +laser
    other="${mode%%+laser}"
    OPT=$(($SPILL_NO % $SPILL_LASER))
    if [ "$OPT" -eq 0 ]; then
        option="laser"
    else
        option="$other"
    fi
else
    option=$mode
fi

echo "spill type is: " $option


SPILL_TYPE="${SPILL}_${option}"


# --- Start global timer ---
start_time=$(date +%s)


UNPACKED_FILE="${RECO_UNPACKED_OUTDIR}/DataTree/$RUN/${SPILL}.root"

if [ "$nounpack" != "nounpack" ]; then
  mkdir -p ${RECO_UNPACKED_OUTDIR}/DataTree/$RUN/
  #EBETE_DIR="/afs/cern.ch/work/m/mcampana/Testbeam/ecal-h4-utils"

  cd ${EBETE_DIR}

  echo "current directory $PWD"

  export PYTHONPATH=$PYTHONPATH:$(pwd)

  echo "Unpacking run $RUN spill $SPILL with EBeTe..."

  #RECO_UNPACKED_OUTDIR="/root/test/DataTree"

  echo "python3 test/unpack_spill.py ${RAW_DIR}/$RUN/$SPILL.raw ${UNPACKED_FILE}"
  #python3 test/unpack_spill.py ${RAW_DIR}/$RUN/$SPILL.raw ${UNPACKED_FILE} > ${RECO_UNPACKED_OUTDIR}/DataTree/$RUN/${SPILL}.txt
  python3 test/unpack_spill.py ${RAW_DIR}/$RUN/$SPILL.raw ${UNPACKED_FILE}

  echo "Unpacked DONE for run $RUN spill $SPILL with EBeTe..."
fi

cd $WORKING_DIR
echo $PWD
mkdir -p ${RECO_UNPACKED_OUTDIR}/reco/run_$RUN/

if [ "$doplots" == "1" ]; then
  mkdir $PLOT_MAIN_FOLDER/prova_mattia_run_$RUN/
  PLOT_CURRENT_FOLDER=$PLOT_MAIN_FOLDER/prova_mattia_run_$RUN/spill_$SPILL_TYPE/

  mkdir $PLOT_CURRENT_FOLDER

  #/bin/cp *.php $PLOT_MAIN_FOLDER
  /bin/cp ferrari_core/php/*.php $PLOT_MAIN_FOLDER/prova_mattia_run_$RUN/
  /bin/cp ferrari_core/php/*.php $PLOT_CURRENT_FOLDER
  echo "plotting in: $PLOT_CURRENT_FOLDER"

  plots_options="-p plotlists/plot_list_$option.csv -po $PLOT_CURRENT_FOLDER"
else
  plots_options=""
fi

echo "Starting reconstruction..."

export PYTHONPATH=$PWD:$PYTHONPATH
echo "$PYTHONPATH"

python3 -m ferrari_core.reco -i ${UNPACKED_FILE} \
    -r "$RUN" \
    -s "$SPILL" \
    -ro ${RECO_UNPACKED_OUTDIR}/reco/run_$RUN/ \
    -j confs/detectors_conf.json \
    -opt $option \
    --do-plots $doplots $plots_options

end_time=$(date +%s)
total_time=$((end_time - start_time))
echo "Total elapsed time: $total_time seconds."

if [ "$doplots" == "1" ]; then
  cp -rT "$PLOT_MAIN_FOLDER/run_$RUN/spill_$SPILL_TYPE" "$PLOT_MAIN_FOLDER/run_$RUN/${option}_current_spill"

  echo $option
  if [ "$option" == "beam" ]; then
    echo "writing folder path to hadd buffer"
    echo $PLOT_MAIN_FOLDER/run_$RUN/spill_$SPILL_TYPE >> $PLOT_MAIN_FOLDER/to_hadd_buffer.txt
  fi

  if [ "$option" == "beam" ] && [ $((SPILL_NO % SPILL_REP)) -eq $((SPILL_REP - 1)) ]; then
    cp $PLOT_MAIN_FOLDER/to_hadd_buffer.txt $PLOT_MAIN_FOLDER/to_hadd_now.txt
  fi
fi
