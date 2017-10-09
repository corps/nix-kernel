from ipykernel.kernelapp import IPKernelApp
from .kernel import NixKernel
IPKernelApp.launch_instance(kernel_class=NixKernel)
