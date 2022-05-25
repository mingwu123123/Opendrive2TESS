# pyd所在路径
module_name = "Tessng" # pyd文件必须放在script目录下执行

exec("import %s" % module_name)

from pybind11_stubgen import ModuleStubsGenerator

module = ModuleStubsGenerator(module_name)
module.parse()
module.write_setup_py = False

with open(f"stubshome/{module_name}.pyi", "w") as fp:
    fp.write("#\n# Automatically generated file, do not edit!\n#\n\n")
    fp.write("\n".join(module.to_lines()))