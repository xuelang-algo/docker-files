FROM datmo/dl-deps:cpu-py35

MAINTAINER Datmo devs <dev@datmo.com>

ARG OPENCV_VERSION=3.2.0
ARG TENSORFLOW_VERSION=v1.8.0
ARG KERAS_VERSION=2.1.6

RUN pip --no-cache-dir install \
        Cython \
        h5py \
        ipykernel \
        jupyter \
        matplotlib \
        numpy \
        pandas \
        path.py \
        pyyaml \
        scipy \
        six \
        sklearn \
        sympy \
        Pillow \
        zmq \
        dlib \
        gym[all] \
        incremental \
        nltk \
        textacy \
        scikit-image \
        spacy \
        tqdm \
        wheel

# Install xgboost
RUN git clone --recursive https://github.com/dmlc/xgboost \
    && cd xgboost \
    && make -j$(nproc) \
    && cd python-package \
    && python setup.py install \
    && cd ../.. \
    && rm -rf xgboost

RUN apt-get update && apt-get install -y \
        python-opencv \
        libavcodec-dev \
        libavformat-dev \
        libav-tools \
        libavresample-dev \
        libdc1394-22-dev \
        libgdal-dev \
        libgphoto2-dev \
        libgtk2.0-dev \
        libjasper-dev \
        liblapacke-dev \
        libopencore-amrnb-dev \
        libopencore-amrwb-dev \
        libopencv-dev \
        libopenexr-dev \
        libswscale-dev \
        libtbb2 \
        libtbb-dev \
        libtheora-dev \
        libv4l-dev \
        libvorbis-dev \
        libvtk6-dev \
        libx264-dev \
        libxine2-dev \
        libxvidcore-dev \
        qt5-default \
        && \
    apt-get clean && \
    apt-get autoremove && \
    rm -rf /var/lib/apt/lists/*

RUN cd ~/ && \
    git clone https://github.com/Itseez/opencv.git --branch ${OPENCV_VERSION} --single-branch && \
    git clone https://github.com/Itseez/opencv_contrib.git --branch ${OPENCV_VERSION} --single-branch && \
    cd opencv && \
    mkdir build && \
    cd build && \
    cmake -D CMAKE_BUILD_TYPE=RELEASE \
        -DWITH_QT=ON \
        -DWITH_OPENGL=ON \
        -D ENABLE_FAST_MATH=1 \
        -DFORCE_VTK=ON \
        -DWITH_TBB=ON \
        -DWITH_GDAL=ON \
        -DWITH_XINE=ON \
        -DBUILD_EXAMPLES=ON \
        -D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib/modules \
        .. && \
    make -j"$(nproc)" && \
    make install && \
    ldconfig && \
 # Remove the opencv folders to reduce image size
    rm -rf ~/opencv*


RUN git clone https://github.com/tensorflow/tensorflow.git --branch ${TENSORFLOW_VERSION} --single-branch
WORKDIR /tensorflow

ENV CI_BUILD_PYTHON python



# install mock for py2 build
RUN python --version 2>&1 | grep 'Python 2' \
    && pip --no-cache-dir install \
        mock \
        && rm -rf /pip_pkg \
        && rm -rf /tmp/* \
        && rm -rf /root/.cache \
    || true


# NOTE: This command uses special flags to build an optimized image for AWS machines.
# This image might *NOT* work on other machines
# Clean up pip wheel and Bazel cache when done.
RUN tensorflow/tools/ci_build/builds/configured CPU \
    bazel build -c opt --copt=-msse3 --copt=-msse4.1 --copt=-msse4.2 \
        --copt=-mavx --copt=-mavx2 \
        --copt=-mfma \
        --cxxopt="-D_GLIBCXX_USE_CXX11_ABI=0" \
         \
        --verbose_failures \
        tensorflow/tools/pip_package:build_pip_package \
    && bazel-bin/tensorflow/tools/pip_package/build_pip_package /tmp/pip \
    && pip --no-cache-dir install --upgrade /tmp/pip/tensorflow-*.whl \
    && rm -rf /pip_pkg \
    && rm -rf /tmp/* \
    && rm -rf /root/.cache \
    && cd / && rm -rf tensorflow

WORKDIR /

# Install Keras and tflearn
RUN pip --no-cache-dir install \
        git+git://github.com/fchollet/keras.git@${KERAS_VERSION} \
        tflearn==0.3.2 \
    && rm -rf /pip_pkg \
    && rm -rf /tmp/* \
    && rm -rf /root/.cache