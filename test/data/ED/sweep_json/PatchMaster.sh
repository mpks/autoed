module load nexgen
nexgen_phil get ED_Singla.phil -o .

ED_nexus singla ED_Singla.phil\
                                              input.datafiles=./20240229_1435_nav6_305.-474.47._Lab6_hopefully_data_000001.h5\
                                              goniometer.starts=-60,0,0,0\
                                              goniometer.increments=0.1,0,0,0\
                                              goniometer.vectors=0,-1,0,0,0,1,0,1,0,1,0,0\
                                              detector.starts=785.91\
                                              beam.wavelength=0.02508\
                                              -m ./20240229_1435_nav6_305.-474.47._Lab6_hopefully_master.h5
