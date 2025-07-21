#!/bin/bash

# Usage: ./validate_epub_maven.sh <epubfile>

set -e

if [ -z "$JAVA_HOME" ]; then
    echo "ERROR: JAVA_HOME is not set."
    exit 1
fi

if [ ! -x "$JAVA_HOME/bin/java" ]; then
    echo "ERROR: JAVA_HOME does not point to a valid Java binary."
    exit 2
fi

if ! command -v mvn &> /dev/null; then
    echo "ERROR: Maven (mvn) is not installed or not in your PATH."
    exit 3
fi

if [ ! -f "pom.xml" ]; then
    echo "ERROR: No pom.xml found in the current directory."
    exit 4
fi

if [ $# -lt 1 ]; then
    echo "Usage: $0 <epubfile>"
    exit 5
fi

EPUBFILE="$1"

if [ ! -f "$EPUBFILE" ]; then
    echo "ERROR: EPUB file '$EPUBFILE' does not exist."
    exit 6
fi

echo "JAVA_HOME: $JAVA_HOME"
echo "Java version: $("$JAVA_HOME/bin/java" -version 2>&1 | head -n 1)"
echo "Maven version: $(mvn -version 2>&1 | head -n 1)"

# Run epubcheck via Maven
mvn compile exec:java -Dexec.args="$EPUBFILE"