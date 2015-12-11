#!/usr/bin/evn python

import commands
import os
import glob
import logging
import time

logger = logging.getLogger()
logging.basicConfig( format  = '%(asctime)s: %(message)s', datefmt = '%m/%d/%y %I:%M:%S', filename = 'final.log', filemode = 'w', level   = logging.INFO )

#s2_result_path = "/data/celpp/2015/dataset.week.47/stage.2.blastnfilter"
#pdb_protein_location = "/data/pdb.extracted"
#full_copy_location = ""
#target_copy_location = ""

def extract_info_from_s2(stage_2_out):
    info_dic = {}
    f = open(stage_2_out,"r")
    lines = f.readlines()
    f.close()
    for line in lines:
        #print line.split(",")[0]
        info_title = line.split(",")[0]
        info_value_1 = line.split(",")[1] 
        if line.split(",")[0] == "inchi":
            info_title = line.split(", InChI=")[0] 
            info_value_1 = line.split(", InChI=")[1].split("\n")[0]
        else:
            try:
                info_value_2 = line.split(",")[2].split("\n")[0].strip()
                info_title = line.split(",")[0]
                info_value_1 = line.split(",")[1].strip() 
            except:
                info_value_2 = False
                info_title = line.split(",")[0]
                info_value_1 = line.split(",")[1].split("\n")[0].strip()
                pass
        #if not 
        if not info_value_2:
            info_dic[info_title] = info_value_1
        else:
            info_dic[info_title] = (info_value_1,info_value_2) 
    return info_dic

#copy all the txt files from the output stage 2 location and create folder for each of this named by the query entry
#check if it finished later needed 
def get_center(protein_file, ligname):
    xyz_lines = open(protein_file,"r").readlines()
    multi_ligand = False
    atom_list = []
    x = y = z = 0
    for xyz_line in xyz_lines:
        if "HETATM" in xyz_line and ligname in xyz_line:
            atom_name = xyz_line[12:16]
            if atom_name in atom_list:
                multi_ligand = True
            else:
                atom_list.append(atom_name)
                x += float(xyz_line[30:38])
                y+= float(xyz_line[38:46])
                z+= float(xyz_line[46:54])
    if not multi_ligand:
        lig_center = "%8.3f, %8.3f, %8.3f"%(x/len(atom_list), y/len(atom_list), z/len(atom_list))
        return lig_center
    else:
        return False

def ligand_prepare(ligand_smile, out_lig_file):
    print "Something wrong...", ligand_smile, out_lig_file
    commands.getoutput("$SCHRODINGER/ligprep -WAIT -i 0 -nt -s 1 -g -ismi %s -omae %s"%(ligand_smile, out_lig_file) ) 
    return os.path.isfile(out_lig_file)

def align_proteins (target_protein, pre_prepare_protein, post_prepare_protein):
    commands.getoutput("$SCHRODINGER/utilities/structalign %s %s"%(target_protein, pre_prepare_protein))
    rotated_protein = "rot-" + pre_prepare_protein
    if os.path.isfile(rotated_protein):
        commands.getoutput("mv %s %s"%(rotated_protein, post_prepare_protein))
        return True
    else:
        return False

def split_complex (part, complex_file, out_split):
    commands.getoutput("$SCHRODINGER/run split_structure.py -many_files -m %s %s %s"%(part, complex_file, out_split))
    out_receptor = os.path.splitext(out_split)[0] + "_receptor1"+ os.path.splitext(out_split)[1]
    if os.path.isfile(out_receptor):
        return out_receptor 
    else:
        return False

def prepare_protein (protein_file, prepared_protein, sleep_time = 300):
    #here the prepared protein should has ".maegz" as extension
    commands.getoutput("$SCHRODINGER/utilities/prepwizard %s %s"%(protein_file, prepared_protein))
    time.sleep(sleep_time) 
    if os.path.isfile(prepared_protein):
        return True
    else:
        return False


def main_proteinprep ( s2_result_path, pdb_protein_path, working_folder ):
    os.chdir(working_folder)
    current_dir_layer_1 = os.getcwd()
    all_stage_2_out = glob.glob("%s/*.txt"%s2_result_path)
    summary_file = "%s/summary.txt"%s2_result_path
    if summary_file in all_stage_2_out:
        all_stage_2_out.remove(summary_file)
    for single_stage_2_out in all_stage_2_out: 
        query_pro = os.path.basename(single_stage_2_out).split(".txt")[0]
        if not os.path.isdir(query_pro):
            os.mkdir(query_pro)
        os.chdir(query_pro)
    #+++++++++++++++++++++
    #get the infromation from stage 2 output
        commands.getoutput("cp %s ."%single_stage_2_out)
        query_dic = extract_info_from_s2(query_pro + ".txt")
        print "QQQQQQQQQQQQQQQQQ", query_dic
        #raw_input()
    
    ######################
    #step 1, check if there is a protein start with largest if not then don't need to continue
    ######################
        if not "largest" in query_dic:
            logging.info("For this query protein: %, there is no protein sharing the largest ligand witt. Not able to generate Docking grid, pass for this case..."%query_pro)
            os.chdir(current_dir_layer_1)     
            continue
        elif len(query_dic["largest"]) != 2:
            logging.info("For this query protein: %s, the laregest protein has wrong number of informations associate with this id..."%query_pro)
            os.chdir(current_dir_layer_1)
            continue
        elif not "inchi" in query_dic:
            logging.info("For this query protein: %, there is no inchi info for the ligand..."%query_pro)
            os.chdir(current_dir_layer_1)
            continue
        else:
            print "Comes to here for this case!!!!!!!!"
            #raw_input()
        ######################
        #step 2, if there is a largest protein then copy this portein to this folder and generate the center of the ligand
        ######################
            largest_pro_id = query_dic["largest"][0]
            largest_pdb_folder_name = largest_pro_id[1:3]
            largest_ent_file = "pdb" + largest_pro_id  + ".ent"
            largest_pdbloc = os.path.join(pdb_protein_path, largest_pdb_folder_name, largest_ent_file)
            if not os.path.isfile(largest_pdbloc):
                logging.info("Unable to find the ent file associate with the largest pdb: %s at location %s"%(largest_pro_id, largest_pdbloc)) 
                os.chdir(current_dir_layer_1)
                continue
            else:
                commands.getoutput("cp %s largest.pdb"%(largest_pdbloc))
        ######################
        #step 3, get the center of the ligand in the largest pdb
        ######################
        try:
            largest_ligand = query_dic["largest"][1] 
        except:
            logging.info("There is no ligand information for this largest protein: %s"%(largest_pro_id))
            os.chdir(current_dir_layer_1)
            continue
        ligand_center = get_center ("largest.pdb", largest_ligand) 
        if not ligand_center:
            logging.info("Unable to find the center of the ligand for the largest pdb: %s"%(largest_pro_id))
            os.chdir(current_dir_layer_1)
            continue
        else:
            center_file = open("center.txt", "w")
            center_file.writelines(ligand_center)
            center_file.close()
        ######################
        #step 4, prepare the ligand 
        ######################
        #a. generate the smile string from inchi 
        ligand_inchi = "InChI=" + query_dic["inchi"]
        inchi_f = open("tmp.inchi", "w")
        inchi_f.writelines(ligand_inchi)
        inchi_f.close()
        inchi_filename = "tmp.inchi"
        smile_filename = "tmp.smi"
        #print "babel -iinchi %s  -osmi ---errorlevel 1"%inchi_filename
        commands.getoutput("babel -iinchi %s  -osmi %s ---errorlevel 1"%(inchi_filename, smile_filename))
        #raw_input()
        if os.path.isfile(smile_filename):
            smile_file = open(smile_filename, "r")
            ligand_smile = smile_file.readlines()
            smile_file.close()
        else:
            logging.info( "Convert from inchi:%s to smile failed"%s(ligand_inchi))
        #finish generating the smiles, then try to prepared the ligand 
        ##############ligand prep step starts here##############
        #if not ligand_prepare(ligand_smile, "ligand.mae"):
        if not ligand_prepare(smile_filename, "ligand.mae"):
            logging.info("Unable to prepare the ligand for this query protein:%s"%query_pro)
            os.chdir(current_dir_layer_1)
            continue 
        else:
        ########################################################
        #step 5, align all proteins
            for rest_protein in ("smallest", "holo", "apo"):
                if rest_protein in query_dic:
                    #copy to here
                    if len(query_dic[rest_protein]) == 2:
                        #have both id and ligand info
                        rest_protein_id = query_dic[rest_protein][0]
                    else:
                        #have only id info 
                        rest_protein_id = query_dic[rest_protein]
                    print "DDDDDDDDDDDDDDDDD", query_dic, rest_protein, rest_protein_id
                    rest_protein_folder_name = rest_protein_id[1:3]
                    rest_ent_file = "pdb" + rest_protein_id  + ".ent"
                    rest_pdbloc = os.path.join(pdb_protein_path, rest_protein_folder_name, rest_ent_file)
                    if not os.path.isfile(rest_pdbloc):
                        logging.info("Unable to find the ent file associate with the %s pdb with ID: %s at location %s"%(rest_protein, rest_protein_id, largest_pdbloc))
                        os.chdir(current_dir_layer_1)
                        continue
                    else:
                        rest_protein_name = rest_protein + ".pdb"
                        commands.getoutput("cp %s %s"%(rest_pdbloc, rest_protein_name))
                    align_proteins ("largest.pdb", rest_protein_name, rest_protein_name)
        ######################
        #step 6, prepare all proteins
        ######################
        for all_protein in ("largest", "smallest", "holo", "apo"):
            all_protein_full_name = all_protein+".pdb"
            if os.path.isfile(all_protein_full_name):
                #split the complex first
                out_split = all_protein+ "_splitted.pdb"
                out_receptor = split_complex("pdb", all_protein_full_name, out_split)
                if not out_receptor:
                    logging.info("Unable to split this protein:%s"%(all_protein_full_name))
                else:
                    logging.info("Succsessfully split this protein:%s, go to preparation step"%(all_protein_full_name))
                    prepared_protein_maegz = all_protein + ".maegz"
                    #pass the wizard sleep time here
                    preparation_result = prepare_protein(out_receptor,prepared_protein_maegz, 1 )
                    if not preparation_result:
                        logging.info("Unable to prepare this protein:%s"%(out_split))
                    else:
                        logging.info("Succsessfully prepared this protein:%s"%(prepared_protein_maegz))
                        #convert into pdb format
                        out_prepare_pdb = all_protein_full_name + "_prepared.pdb"
                        commands.getoutput("$SCHRODINGER/utilities/pdbconvert -imae %s -opdb %s"%(prepared_protein_maegz, out_prepare_pdb))
        os.chdir(current_dir_layer_1)
                    
                

if ("__main__") == (__name__):
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-p", "--pdbloc", metavar = "PATH", help = "PDB DATABANK which we will dock into")
    parser.add_option("-l", "--locs2", metavar="PATH", help = "PATH where we could find the stage 2 output")
    parser.add_option("-w", "--wfolder", metavar = "PATH", help = "PATH where we run stage 3")
    #parser.add_option("-s", "--sleep", metavar = "VALUE", help = "Sleep time for protein prep")
    #parser.add_option("-u", "--update", default = False, action = "store_true", help = "update the protein generation and docking step")
    logger = logging.getLogger()
    logging.basicConfig( format  = '%(asctime)s: %(message)s', datefmt = '%m/%d/%y %I:%M:%S', filename = 'final.log', filemode = 'w', level   = logging.INFO )
    (opt, args) = parser.parse_args()
    pdb_location = opt.pdbloc
    stage_2_result = opt.locs2
    stage_3_result = opt.wfolder
    #sleep_time = opt.sleep
    main_proteinprep(stage_2_result, pdb_location, stage_3_result)
    
    
    

