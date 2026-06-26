# Installation

## Python environment

Requires Python 3.10 or later.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

For development tools (linting, tests):

```bash
pip install -e ".[dev]"
```

## OpenMVG

OpenMVG provides the sparse Structure-from-Motion stage. The pipeline calls its binaries via `subprocess`, so they must be on `PATH`.

### From prebuilt packages (Ubuntu/Debian)

```bash
sudo apt install libopenmvg-dev openmvg-bin
```

### From source

```bash
sudo apt install libpng-dev libjpeg-dev libtiff-dev libxxf86vm1 libxxf86vm-dev \
    libxi-dev libxrandr-dev graphviz coinor-libclp-dev libceres-dev

git clone --recursive https://github.com/openMVG/openMVG.git
cmake -S openMVG/src -B openMVG/build \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr/local
cmake --build openMVG/build --parallel
sudo cmake --install openMVG/build
```

Verify:

```bash
openMVG_main_SfMInit_ImageListing --help
```

## OpenMVS

OpenMVS provides dense point cloud computation, mesh reconstruction, and texturing.

### Dependencies

```bash
sudo apt install libboost-iostreams-dev libboost-program-options-dev libboost-system-dev \
    libboost-serialization-dev libopencv-dev libcgal-dev libatlas-base-dev libeigen3-dev \
    libvtk9-dev
```

CUDA is optional but strongly recommended for `DensifyPointCloud`:

```bash
# Verify CUDA toolkit is installed
nvcc --version
```

### From source

```bash
git clone --recursive https://github.com/cdcseacave/openMVS.git
cmake -S openMVS -B openMVS/build \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DOpenMVS_USE_CUDA=ON
cmake --build openMVS/build --parallel
sudo cmake --install openMVS/build
```

Verify:

```bash
DensifyPointCloud --help
TextureMesh --help
```

## Arduino firmware

The turntable stepper motor is controlled by an Arduino Nano running the firmware in `hardware/turntable/`. Flash it with the Arduino IDE or `arduino-cli`:

```bash
arduino-cli compile --fqbn arduino:avr:nano hardware/turntable/
arduino-cli upload  --fqbn arduino:avr:nano --port /dev/ttyUSB0 hardware/turntable/
```

## Verify the full stack

```bash
python - <<'EOF'
import cv2, numpy, open3d
print("cv2", cv2.__version__)
print("numpy", numpy.__version__)
print("open3d", open3d.__version__)
EOF

openMVG_main_SfMInit_ImageListing --version
DensifyPointCloud --version
```
