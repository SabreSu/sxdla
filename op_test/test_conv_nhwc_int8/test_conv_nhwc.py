# Copyright [2022] <USTC-CSS lab>
"""Test cases about conv_nhwc"""
# pylint: disable=wrong-import-position
import sys
sys.path.append("../")
# pylint: disable=unused-wildcard-import, wildcard-import
from util import *  

import tvm

# pylint: disable=line-too-long,missing-function-docstring,too-many-arguments
def verify_conv_nhwc_int8_old(feature_map_shape, weight_shape, origin_file, dtype="int8", stride=1, padding=1):
  cmd_str = "../../assembler/as operators/{}".format(origin_file)
  as_out = "as_out"
  as_out = call_assembler(cmd_str, as_out)
  # generate "cmd.dat" file.
  # 1. get command fields from assembler output.
  param_dic = get_cmd_fields(as_out)
  # 2. translate command data form.
  param_dic = translate_cmd_data_form(param_dic)
  # 3. generate weight data.
  weight_list = gen_weight_data(weight_shape, dtype)
  weight_list_str = gen_weight_data_str(weight_list)
  
  # (fixme)TODO(ssb)：When the assembler is finished, change this step to
  #                   write the weight data into the weight file. And execute
  #                   the assembler after this step, taking the weight data
  #                   file as an input of the assembler.
  # write_weight_file(weight_list_str)

  # 4. write command and weight data to "cmd.dat" file.
  write_command(param_dic, weight_list_str, "cmd.dat")

  # generate "data.dat" file.

  # verify the output of "sxdla"
  # 1. get result of python conv.
  dw_np = tvm.topi.testing.dilate_python(weight_list, (1, 1, 1, 1))
  b_np = tvm.topi.testing.conv2d_nhwc_python(feature_map, dw_np, stride, padding)

  # 2. run "sxdla"
  subprocess.run("sxdla", shell=True)

  subprocess.run("cp data.dat mem.dat", shell=True)
  # 3.verify the result
  # try:
  #   verify_result(b_np, [1, 56, 56, 1], "mem.dat")
  # except Exception as e:
  #   print(e)
  verify_result(b_np, [1, 56, 56, 1], "mem.dat")

def verify_conv_nhwc_int8(feature_map_shape, weight_shape, origin_file, weight_file, dtype="int8", stride=1, padding=1, rand_type="rand"):
  # 1. Generate weight data and write to a weight file.
  weight_list = gen_weight_data(weight_shape, dtype, rand_type)
  weight_list_str = gen_weight_data_str(weight_list)
  write_weight_file(weight_list_str, "weight.dat")
  
  # 2. Call assembler and generate a "bin" file.
  subprocess.run("../../assembler/as operators/{}  {}  {}".format(origin_file, weight_file, "bin.dat"), shell=True)
  
  # 3. Remove the 64 bit data in the header of the bin file.
  remove_head(file_name = "byte_per_line")
  
  # 4. Generate input data and write to "data.dat" file.
  feature_map = gen_feature_map_data(feature_map_shape, dtype, rand_type)
  feature_map_str = numpyint8_2_hexstring(feature_map)
  write_data(feature_map_str, "data.dat")

  # 5. Run dla
  subprocess.run("sxdla", shell=True)
  
  # 6. Parse "mem.dat" file and verify the result.
  dw_np = tvm.topi.testing.dilate_python(weight_list, (1, 1, 1, 1))
  b_np = tvm.topi.testing.conv2d_nhwc_python(feature_map, dw_np, stride, padding)
  verify_result(b_np, feature_map_shape, weight_shape, "mem.dat")

def test_conv_nhwc_int8():
  verify_conv_nhwc_int8([1, 56, 56, 1], [3, 3, 1, 1], "conv_nhwc_int8_56", "weight.dat", rand_type="ones")
  verify_conv_nhwc_int8([1, 28, 28, 1], [3, 3, 1, 1], "conv_nhwc_int8_28", "weight.dat", rand_type="ones")
  verify_conv_nhwc_int8([1, 63, 63, 1], [3, 3, 1, 1], "conv_nhwc_int8_63", "weight.dat", rand_type="ones")
  verify_conv_nhwc_int8([1, 56, 56, 1], [3, 3, 1, 1], "conv_nhwc_int8_56", "weight.dat")
  verify_conv_nhwc_int8([1, 28, 28, 1], [3, 3, 1, 1], "conv_nhwc_int8_28", "weight.dat")
  verify_conv_nhwc_int8([1, 63, 63, 1], [3, 3, 1, 1], "conv_nhwc_int8_63", "weight.dat")
  verify_conv_nhwc_int8([1, 1, 1, 1], [3, 3, 1, 1], "conv_nhwc_int8_56", "weight.dat")
  #verify_conv_nhwc_int8([1, 64, 64, 1], [3, 3, 1, 1], "conv_nhwc_int8_64", "weight.dat")
  # clean up temporary files.
  clean_up_tmp_files()


if __name__ == "__main__":
  test_conv_nhwc_int8()
