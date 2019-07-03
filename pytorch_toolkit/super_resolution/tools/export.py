#!/usr/bin/env python3
#
# Copyright (C) 2019 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions
# and limitations under the License.

import argparse
import os
import subprocess
import torch.onnx
from sr.trainer import Trainer

def parse_args():
    parser = argparse.ArgumentParser(description="PyTorch SR export to onnx and IR")
    parser.add_argument("--exp_name", default="test", type=str, help="experiment name")
    parser.add_argument("--models_path", default="./models", type=str, help="path to models folder")
    parser.add_argument("--input_size", type=int, nargs='+', default=(200, 200), help="Input image size")
    parser.add_argument("--scale", type=int, default=4, help="Upsampling factor for SR")
    parser.add_argument('--data_type', default='FP32', choices=['FP32', 'FP16'], help='Data type of IR')
    parser.add_argument('--output_dir', default=None, help='Output Directory')
    return parser.parse_args()

def execute_mo(input_model, output_dir, name, data_type):
    command = [
        'mo.py',
        '--input_model={}'.format(input_model),
        '--output_dir={}'.format(output_dir),
        '--model_name={}'.format(name),
        '--data_type={}'.format(data_type)
    ]
    subprocess.call(command)

def main():
    opt = parse_args()

    models_path = opt.models_path
    name = opt.exp_name
    input_size = opt.input_size
    scale = opt.scale

    x = torch.randn(1, 3, input_size[0], input_size[1], requires_grad=True).cuda()
    cubic = torch.randn(1, 3, scale*input_size[0], scale*input_size[1], requires_grad=True).cuda()

    trainer = Trainer(name=name, models_root=models_path, resume=True)
    trainer.load_latest()

    trainer.model = trainer.model.train(False)

    model_dir = os.path.join(models_path, name)

    export_dir = opt.output_dir if opt.output_dir else os.path.join(model_dir, 'export')
    model_onnx_path = os.path.join(export_dir, "model.onnx")

    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    torch.onnx.export(trainer.model,  # model being run
                      [x, cubic],  # model input (or a tuple for multiple inputs)
                      model_onnx_path,  # where to save the model
                      export_params=True,
                      verbose=True)  # store the trained parameter weights inside the model file

    ir_export_dir = os.path.join(export_dir, 'IR', opt.data_type)
    execute_mo(model_onnx_path, ir_export_dir, 'sr', opt.data_type)

if __name__ == "__main__":
    main()
