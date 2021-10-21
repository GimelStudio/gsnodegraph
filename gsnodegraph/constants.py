# ----------------------------------------------------------------------------
# GS Nodegraph Copyright 2019-2021 by Noah Rahm and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ----------------------------------------------------------------------------

SOCKET_RADIUS = 5
SOCKET_HIT_RADIUS = 10

SOCKET_INPUT = 0
SOCKET_OUTPUT = 1

SOCKET_DATATYPES = {
    "RENDERIMAGE": "#C6C62D",
    "VALUE": "#A0A0A0",
}

NODE_CATEGORY_COLORS = {
    "INPUT": "#E64555",  # Burgendy
    "DRAW": "#AF4467",  # Pink
    "MASK": "#084D4D",  # Blue-green
    "CONVERT": "#564B7C",  # Purple
    "VALUE": "#CC783D",  # Orange
    "FILTER": "#558333",  # Green
    "BLEND": "#498DB8",  # Light blue
    "COLOR": "#C2AF3A",  # Yellow
    "TRANSFORM": "#6B8B8B", # Blue-grey
    "OUTPUT": "#B33641",  # Red
    "DEFAULT": "#975B5B"  # Burgendy
}

NODE_DEFAULT_WIDTH = 136
NODE_DEFAULT_HEIGHT = 150
NODE_THUMB_PADDING = 16
NODE_Y_PADDING = 10
