# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2023, Oracle and/or its affiliates.
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

# -----------------------------------------------------------------------------
# utils.py
#
# Contains utility classes and methods.
# -----------------------------------------------------------------------------

from . import errors


class CheckImpls:
    """
    Decorator class which is used on the base implementation method and checks
    to see which implementation is currently being used (and therefore has no
    support for the method). An exception is raised letting the user know which
    implementation does support the method. Currently there are only two
    implementations (thick and thin) so the assumption is made that the
    implementation not currently running does support the method.
    """

    def __init__(self, feature):
        self.feature = feature

    def __call__(self, f):
        feature = self.feature

        def wrapped_f(self, *args, **kwargs):
            class_name = type(self).__name__
            driver_type = "thin" if class_name.startswith("Thick") else "thick"
            errors._raise_err(
                errors.ERR_FEATURE_NOT_SUPPORTED,
                feature=feature,
                driver_type=driver_type,
            )

        return wrapped_f


def params_initer(f):
    """
    Decorator function which is used on the ConnectParams and PoolParams
    classes. It creates the implementation object using the implementation
    class stored on the parameter class. It first, however, calls the original
    method to ensure that the keyword parameters supplied are valid (the
    original method itself does nothing).
    """

    def wrapped_f(self, *args, **kwargs):
        f(self, *args, **kwargs)
        self._impl = self._impl_class()
        if kwargs:
            self._impl.set(kwargs)

    return wrapped_f


def params_setter(f):
    """
    Decorator function which is used on the ConnectParams and PoolParams
    classes. It calls the set() method on the parameter implementation object
    with the supplied keyword arguments. It first, however, calls the original
    method to ensure that the keyword parameters supplied are valid (the
    original method itself does nothing).
    """

    def wrapped_f(self, *args, **kwargs):
        f(self, *args, **kwargs)
        self._impl.set(kwargs)

    return wrapped_f
