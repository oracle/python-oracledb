# -----------------------------------------------------------------------------
# Copyright (c) 2025 Oracle and/or its affiliates.
#
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl and Apache License
# 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose
# either license.
#
# If you elect to accept the software under the Apache License, Version 2.0,
# the following applies:
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------
#
# NAME
#
#   Dockerfile
#
# PURPOSE
#
#   Sample Dockerfile that creates a container image for Python application
#   development and application deployment.  The container has python-oracledb
#   installed, the Apache web server with WSGI, and (optionally) Oracle Instant
#   Client pre-configured.
#
#   The container is for testing and development purposes only.
#
# NOTE
#
#   Read README.md and then use container_build.sh to build the container from
#   this Dockerfile
#

# Variable declaration for base OS
# --------------------------------
ARG OPY_OS_VERSION=8

# Base OS container image details
# -------------------------------
FROM ghcr.io/oracle/oraclelinux:${OPY_OS_VERSION} AS baseos

# OS Username
ARG OPY_USERNAME

# OS Username's Groupname
ARG OPY_GROUPNAME

# Python Version details
ARG OPY_PYTHON_VERSION

# Instant Client Details
ARG OPY_INSTANT_CLIENT_VERSION

# User base directory
ARG OPY_BASEDIR=/opt

# OS User home directory
ARG OPY_OS_USER_HOMEDIR=/home/${OPY_USERNAME}

# Virtual environment directory name
ARG OPY_PYTHON_VIRTUAL_DIRNAME=pyorcldb_env

# OS Version
ARG OPY_OS_VERSION=8

RUN dnf upgrade && \
  # Install latest Instant Client 23ai
  ( ( [ ${OPY_INSTANT_CLIENT_VERSION} == 23 ] && \
      dnf install oracle-instantclient-release-23ai-el${OPY_OS_VERSION} && \
      dnf install oracle-instantclient-basic \
        oracle-instantclient-sqlplus ) || \
    # Install latest Instant Client 21c
    ( [ ${OPY_INSTANT_CLIENT_VERSION} == 21 ] && \
      dnf install oracle-instantclient-release-el${OPY_OS_VERSION} && \
      dnf install oracle-instantclient-basic \
        oracle-instantclient-sqlplus ) || \
    ( [ ${OPY_INSTANT_CLIENT_VERSION} == None ] && \
      echo "Not installing Instant Client" ) || \
    # Install specific Instant Client 19c release update
    ( \
      # Install Instant Client 19c on Oracle Linux 9
      ( ( [ ${OPY_OS_VERSION} == 9 ] && \
          dnf install oracle-instantclient-release-el${OPY_OS_VERSION} && \
          dnf install \
            oracle-instantclient${OPY_INSTANT_CLIENT_VERSION}-basic \
            oracle-instantclient${OPY_INSTANT_CLIENT_VERSION}-sqlplus \
        ) || \
        # Install Instant Client 19c on Oracle Linux 8
        ( dnf install oracle-release-el${OPY_OS_VERSION} && \
          dnf install \
            oracle-instantclient${OPY_INSTANT_CLIENT_VERSION}-basic \
            oracle-instantclient${OPY_INSTANT_CLIENT_VERSION}-sqlplus \
        ) ) ) || \
        ( echo "Not installing Instant Client" ) \
  ) && \
  # Install sudo, openssl and Python
  # Installing ncurses to include 'clear' command
  dnf install sudo openssl apr apr-util ncurses && \
  echo "Python Version - ${OPY_PYTHON_VERSION}" && \
  dnf install python${OPY_PYTHON_VERSION} python${OPY_PYTHON_VERSION}-pip \
  python${OPY_PYTHON_VERSION}-devel && \
  ( ( [ ${OPY_OS_VERSION} == 9 ] && \
    update-alternatives --install /usr/bin/python python \
    /usr/bin/python${OPY_PYTHON_VERSION} 1 ) || \
    ( echo "Not required to set Python default" ) \
  ) && \
  # Add OS user
  useradd -U -d ${OPY_OS_USER_HOMEDIR} ${OPY_USERNAME} && \
  # Enable sudo access for appuser
  echo "%appuser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
  # Create required directories
  mkdir ${OPY_BASEDIR}/downloads && \
  chown ${OPY_USERNAME}:${OPY_GROUPNAME} ${OPY_BASEDIR}/downloads && \
  mkdir ${OPY_BASEDIR}/wallet && \
  chown ${OPY_USERNAME}:${OPY_GROUPNAME} ${OPY_BASEDIR}/wallet && \
  mkdir ${OPY_BASEDIR}/apache && \
  chown ${OPY_USERNAME}:${OPY_GROUPNAME} ${OPY_BASEDIR}/apache && \
  mkdir ${OPY_BASEDIR}/${OPY_PYTHON_VIRTUAL_DIRNAME} && \
  chown ${OPY_USERNAME}:${OPY_GROUPNAME} \
        ${OPY_BASEDIR}/${OPY_PYTHON_VIRTUAL_DIRNAME} && \
  mkdir ${OPY_BASEDIR}/app && \
  chown ${OPY_USERNAME}:${OPY_GROUPNAME} ${OPY_BASEDIR}/app && \
  mkdir ${OPY_BASEDIR}/cert && \
  chown ${OPY_USERNAME}:${OPY_GROUPNAME} ${OPY_BASEDIR}/cert && \
  # Clean up cache
  dnf clean all

FROM baseos AS pythonenv

# OS Username
ARG OPY_USERNAME

# OS Username's Groupname
ARG OPY_GROUPNAME

# Python Version details
ARG OPY_PYTHON_VERSION

# Virtual environment directory name
ARG OPY_PYTHON_VIRTUAL_DIRNAME=pyorcldb_env

# User base directory
ARG OPY_BASEDIR=/opt

# OS User home directory
ARG OPY_OS_USER_HOMEDIR=/home/${OPY_USERNAME}

# Switch User
USER ${OPY_USERNAME}

# Copy Auto deploy script template
COPY --chown=${OPY_USERNAME}:${OPY_GROUPNAME} \
  otherfiles/autodeployscript.sh.template \
  ${OPY_OS_USER_HOMEDIR}/autodeployscript.sh

# Configure virtual environment
RUN cd ${OPY_BASEDIR} && \
  python${OPY_PYTHON_VERSION} -m venv ${OPY_PYTHON_VIRTUAL_DIRNAME} && \
  # Source the Python virtual environment
  source ${OPY_BASEDIR}/${OPY_PYTHON_VIRTUAL_DIRNAME}/bin/activate && \
  # Upgrade pip utility
  python -m pip install --upgrade pip && \
  # Install python-oracledb driver for Python
  # Install wheel module (pre-requisite for WSGI module)
  python -m pip install oracledb wheel && \
  # Configure PATH and set the Python virtual environment user profile
  echo "export PATH=${OPY_BASEDIR}/apache/bin:\$PATH" >> \
    ${OPY_OS_USER_HOMEDIR}/.bashrc && \
  echo "source ${OPY_BASEDIR}/${OPY_PYTHON_VIRTUAL_DIRNAME}/bin/activate" >> \
    ${OPY_OS_USER_HOMEDIR}/.bashrc && \
  echo "if [ ! -f ${OPY_BASEDIR}/cert/certificate.pem ]; then" >> \
    ${OPY_OS_USER_HOMEDIR}/.bashrc && \
  echo "  ~/pyorcldb_generate_cert.sh" >> ${OPY_OS_USER_HOMEDIR}/.bashrc && \
  echo "fi" >> ${OPY_OS_USER_HOMEDIR}/.bashrc && \
  echo "~/autodeployscript.sh" >> ${OPY_OS_USER_HOMEDIR}/.bashrc && \
  echo "" >> ${OPY_OS_USER_HOMEDIR}/.bashrc && \
  sed -i "s/OPY_OSUSERBASEDIR/\\${OPY_BASEDIR}/g" \
    ${OPY_OS_USER_HOMEDIR}/autodeployscript.sh

# Intermediate image for building Apache Server
# ---------------------------------------------
FROM pythonenv AS apachebuildenv

# Variables declaration for ApacheBuildEnv
# ----------------------------------------

# Apache Server Configuration - Version
ARG OPY_APACHE_SERVER_VERSION

# Python Version details
ARG OPY_PYTHON_VERSION
ARG OPY_PYTHON_VERSION_WITHOUTPERIOD

# OS Username
ARG OPY_USERNAME

# OS Username's Groupname
ARG OPY_GROUPNAME

# Virtual environment directory name
ARG OPY_PYTHON_VIRTUAL_DIRNAME=pyorcldb_env

# User base directory
ARG OPY_BASEDIR=/opt

# Apache HTTP Server Listen port number
ARG OPY_APACHE_LISTEN_PORT

# Switch username
USER ${OPY_USERNAME}

# Copy Apache WSGI configuration file template into downloads directory
COPY --chown=${OPY_USERNAME}:${OPY_GROUPNAME} \
  otherfiles/pyorcldb_wsgi.conf.template ${OPY_BASEDIR}/downloads

# Install Apache Server
RUN sudo dnf install \
  # Install prerequisite packages for Apache installation
  gcc make expat-devel pcre-devel apr-devel apr-util-devel \
    redhat-rpm-config openssl-devel perl && \
  # Download Apache server source
  cd ${OPY_BASEDIR}/downloads && \
  curl -o ${OPY_APACHE_SERVER_VERSION}.tar.gz \
    "https://archive.apache.org/dist/httpd/${OPY_APACHE_SERVER_VERSION}.tar.gz" && \
  tar xzvf ${OPY_APACHE_SERVER_VERSION}.tar.gz && \
  cd ${OPY_APACHE_SERVER_VERSION} && \
  # Prepare and install Apache server
  ./configure --enable-ssl --prefix=${OPY_BASEDIR}/apache && \
  make && \
  make install && \
  # Set path of the Perl in Apache's apxs utility. This is required for
  # building wsgi_mod.
  sed -i "s/\/replace\/with\/path\/to\/perl\/interpreter/\/usr\/bin\/perl/g" \
    ${OPY_BASEDIR}/apache/bin/apxs && \
  export PATH=${OPY_BASEDIR}/apache/bin:$PATH && \
  source ${OPY_BASEDIR}/${OPY_PYTHON_VIRTUAL_DIRNAME}/bin/activate &&\
  # Install WSGI module
  python -m pip install mod_wsgi && \
  # Copy the mod_wsgi module from python virtual environment to Apache home
  cp ${OPY_BASEDIR}/${OPY_PYTHON_VIRTUAL_DIRNAME}/lib/python${OPY_PYTHON_VERSION}/site-packages/mod_wsgi/server/mod_wsgi-py${OPY_PYTHON_VERSION_WITHOUTPERIOD}.cpython-${OPY_PYTHON_VERSION_WITHOUTPERIOD}-x86_64-linux-gnu.so \
    ${OPY_BASEDIR}/apache/modules/mod_wsgi.so && \
  # Configure httpd.conf
  # --------------------
  # 1. Removed listening on port 80
  # 2. Enabled SSL module
  # 3. Set default characterset to UTF-8
  cd ${OPY_BASEDIR}/apache/conf && \
  sed -i "s/Listen 80/# Listen 80/g" httpd.conf && \
  sed -i "s/#LoadModule ssl_module/LoadModule ssl_module/g" httpd.conf && \
  echo "AddDefaultCharset UTF-8" >> httpd.conf && \
  echo "Include conf/extra/pyorcldb_wsgi.conf" >> httpd.conf && \
  # Populate pyorcldb_wsgi.conf file into Apache's conf/extra directory
  cd ${OPY_BASEDIR}/apache/conf/extra && \
  cp ${OPY_BASEDIR}/downloads/pyorcldb_wsgi.conf.template \
    ./pyorcldb_wsgi.conf && \
  sed -i "s/OPY_BASEDIR/\\${OPY_BASEDIR}/g" pyorcldb_wsgi.conf && \
  sed -i "s/OPY_PYTHONVIRTUALDIRNAME/${OPY_PYTHON_VIRTUAL_DIRNAME}/g" \
    pyorcldb_wsgi.conf && \
  sed -i "s/OPY_APACHE_LISTEN_PORT/${OPY_APACHE_LISTEN_PORT}/g" \
    pyorcldb_wsgi.conf && \
  rm ${OPY_BASEDIR}/downloads/pyorcldb_wsgi.conf.template && \
  # Clean all cached packages from DNF cache
  sudo dnf clean all && \
  # Clean all downloads directory
  cd ${OPY_BASEDIR}/downloads && \
  rm -rf *

# Python Development Image
# ------------------------
FROM pythonenv AS developmentimage

# OS Username
ARG OPY_USERNAME

# OS Username's Groupname
ARG OPY_GROUPNAME

# OS User home directory
ARG OPY_OS_USER_HOMEDIR=/home/${OPY_USERNAME}

# User base directory
ARG OPY_BASEDIR=/opt

# Image metadata details
ARG OPY_IMAGE_VERSION
ARG OPY_IMAGE_RELEASE_DATE
ARG OPY_IMAGE_RELEASE_STATUS

# Image metadata
# Uncomment the below lines to provide the label information
# LABEL version=
# LABEL release-date=
# LABEL maintainer=
# LABEL release-status=

# Switch to OS user from root
# ---------------------------
USER ${OPY_USERNAME}

WORKDIR ${OPY_OS_USER_HOMEDIR}

# Get Apache Server
COPY --from=apachebuildenv --chown=${OPY_USERNAME}:${OPY_GROUPNAME} \
  ${OPY_BASEDIR}/apache ${OPY_BASEDIR}/apache

# Copy SSL certificate generation script
COPY --chown=${OPY_USERNAME}:${OPY_GROUPNAME} \
  otherfiles/pyorcldb_generate_cert.sh ${OPY_OS_USER_HOMEDIR}/
