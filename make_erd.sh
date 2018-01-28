#!/bin/bash
./manage.py graph_models runner > dat/models.dot
dot -Tpng dat/models.dot -o dat/models.png
