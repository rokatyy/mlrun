# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#

import re
import sys
from os import path

sys.path.insert(0, "..")


def current_version():
    root = path.dirname(path.dirname(path.abspath(__file__)))
    with open(f"{root}/mlrun/__init__.py") as fp:
        for line in fp:
            # __version__ = '0.4.6'
            match = re.search(r"__version__\s*=\s*'([^']+)'", line)
            if match:
                return match.group(1)
    return "UNKNOWN"


# -- Project information -----------------------------------------------------


project = "mlrun"
copyright = "2023, Iguazio"
author = "Iguazio"

master_doc = "contents"

# The short X.Y version
version = current_version()
version = version[: version.rfind(".")]

# The full version, including alpha/beta/rc tags
release = current_version()

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "myst_nb",
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinx_togglebutton",
    "sphinx_design",
    "sphinx_reredirects",
    "versionwarning.extension",
    "sphinxcontrib.mermaid",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = [
    "_templates",
]

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

linkcheck_ignore = {
    r"https:\/\/github\.com\/.*\/.*#L\d+-L\d+",
    # linkcheck doesn't work well with relative paths which contain anchor, so ignore them
    r"^.*\.html#.*$",
    r"^\./[^/]+\.html#.*$",
    r"^\.\./[^/]+\.html#.*$",
    r"^(?!https?:\/\/).*",
    r"http:\/\/localhost:\d+",
}
linkcheck_anchors = True

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

source_suffix = {
    ".rst": "restructuredtext",
    ".ipynb": "myst-nb",
    ".myst": "myst-nb",
    ".md": "myst-nb",
}

# versionwarning configuration
versionwarning_default_message = (
    "This is not the latest documentation. See {stable} instead."
)

versionwarning_message_placeholder = "stable"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

html_theme = "sphinx_book_theme"
html_title = ""
html_logo = "./MLRun_Character.png"
html_favicon = "./favicon.ico"
nb_execution_mode = "off"
html_sourcelink_suffix = ""
autoclass_content = "both"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_css_files = ["custom.css"]

html_theme_options = {
    "github_url": "https://github.com/mlrun/mlrun",
    "repository_url": "https://github.com/mlrun/mlrun",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_edit_page_button": True,
    "path_to_docs": "docs",
    "home_page_in_toc": False,
    "repository_branch": "development",
    "show_navbar_depth": 1,
    "extra_navbar": 'By <a href="https://www.iguazio.com/">Iguazio</a>',
    "extra_footer": "",
}

html_sidebars = {
    "**": ["navbar-logo.html", "search-field.html", "sbt-sidebar-nav.html"]
}

copybutton_selector = "div:not(.output) > div.highlight pre"

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "html_image",
    "html_admonition",
    "replacements",
    "linkify",
    "substitution",
]
myst_url_schemes = ("http", "https", "mailto")
myst_heading_anchors = 2
myst_all_links_external = True

# These substitutions point to the relevant mlrun docs for the current CE version
myst_substitutions = {
    "version": "version",
    "ceversion": "v1.7.0",
    "releasedocumentation": "docs.mlrun.org/en/stable/index.html",
}

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

# Add here external imports:
autodoc_mock_imports = [
    "plotly",
    "sklearn",
    "tensorflow",
    "tensorboard",
    "torch",
    "lightgbm",
    "xgboost",
    "onnx",
]

redirects = {
    "runtimes/functions-architecture": "runtimes/functions.html",
    "monitoring/initial-setup-configuration": "monitoring/model-monitoring-deployment.html",
    "tutorials/05-batch-infer": "tutorials/06-batch-infer.html",
    "tutorials/06-model-monitoring": "tutorials/05-model-monitoring.html",
    "monitoring/models": "../model-monitoring/monitoring-models.html",
    "monitoring/monitoring": "../model-monitoring.html",
    "monitoring/monitoring-deployment": "../model-monitoring/model-monitoring-deployment.html",
    "monitoring/legacy-model-monitoring": "../model-monitoring/legacy-model-monitoring.html",
    "concepts/monitoring": "model-monitoring.html",
    "monitoring/index": "../model-monitoring/index.html",
    "monitoring/model-monitoring": "monitoring/model-monitoring-flow.html",
}

smartquotes = False

# -- Autosummary -------------------------------------------------------------

autosummary_generate = True


def copy_doc(src, dest, title=""):
    """Copy over .md documentation from other parts of the project"""
    with open(dest, "w") as out:
        with open(src) as fp:
            changed = False
            for line in fp:
                if title and re.match("^# .*", line) and not changed:
                    line = f"# {title}"
                    changed = True
                out.write(line)


def setup(app):
    pass


#   project_root = path.dirname(path.dirname(path.abspath(__file__)))
#   copy_doc(f"{project_root}/examples/remote.md", "external/remote.md")
#    copy_doc(
#        f'{project_root}/README.md', 'external/general.md', 'Introduction')
#    copy_doc(
#        f'{project_root}/hack/local/README.md', 'external/install.md')
#    check_call([
#        'jupyter', 'nbconvert',
#        '--output', f'{project_root}/docs/external/basics.html',
#        f'{project_root}/examples/mlrun_basics.ipynb',
#    ])
