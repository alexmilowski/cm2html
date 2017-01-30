import CommonMark
import argparse,io,sys,os
from shutil import copyfile
from ast import literal_eval

from .util import text,findTitle,toc,dataURI,writeTOC

class HTML5Renderer(CommonMark.HtmlRenderer):
   def attrs(self, node):
      atts = super(HTML5Renderer,self).attrs(node)
      if hasattr(node,'id'):
         atts.append(['id',node.id])
      return atts


   
   
def main():

   prolog = """
   <meta charset="utf-8">
   <link rel="stylesheet" href="http://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.7.0/styles/default.min.css">
   <script src="http://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.7.0/highlight.min.js"></script>
   <script>hljs.initHighlightingOnLoad();</script>
   """
   links = [ ('stylesheet','text/css','default.css')]
   scripts = [ ]
   known_types = {
     'css' : ('stylesheet','text/css'),
     'js' : ('script','text/javascript')
   }

   parser = argparse.ArgumentParser(description="CommonMark to HTML5 processor")
   parser.add_argument(
        'infile',
        nargs="?",
        type=argparse.FileType('r'),
        default=sys.stdin,
        help="The Markdown file to parse (defaults to STDIN)")
   parser.add_argument(
        '-o',
        nargs="?",
        type=argparse.FileType('w'),
        default=sys.stdout,
        help="The output HTML file to produce (defaults to STDOUT)")
   parser.add_argument(
        '--inline',
        action='store_true',
        default=False,
        help="Inline resources via data uris")
   parser.add_argument(
        '--toc',
        action='store_true',
        default=False,
        help="Generate a table of contents")
   parser.add_argument(
        '--autonumber-title',
        action='store_true',
        dest='autonumbertitle',
        default=False,
        help="Generate the title in the table of contents")
   parser.add_argument(
        '--autonumber',
        action='store_true',
        dest='autonumber',
        default=False,
        help="Generate the title in the table of contents")
   parser.add_argument(
        '--prolog',
        type=argparse.FileType('r'),
        dest='prologFile',
        nargs="?",
        help="A file to embed in the prolog (head).")
   parser.add_argument(
        '--link',
        action='append',
        dest='links',
        help="A link to add to the prolog (head)")
   parser.add_argument(
        '--copy-style',
        action='append',
        dest='copyStyle',
        help="Copy the default style from the package to the local destination")
   parser.add_argument(
        '--script',
        action='append',
        dest='scripts',
        help="A script to add to the prolog (head)")
   args = parser.parse_args()

   if args.copyStyle is not None:
      for source in args.copyStyle:
         this_dir, this_filename = os.path.split(__file__)
         path = os.path.join(this_dir, source)
         copyfile(path,source)
      
   f = args.infile
   o = args.o
   s = io.StringIO()
   for line in f:
      s.write(line)
   parser = CommonMark.Parser()
   ast = parser.parse(s.getvalue())
   s.close()
   
   if args.prologFile is not None:
      s = io.StringIO()
      for line in args.prologFile:
         s.write(line)
      prolog = s.getvalue()
      s.close()

   if args.links is not None:
      links = []
      for link in args.links:
         if link[0] == '(':
            links.append(literal_eval(link))
         else:
            ext = link[link.rfind('.')+1:]
            if ext in known_types:
               info = known_types[ext]
               links.append((info[0],info[1],link))
            else :
               raise ValueError('Unknown extension: '+ext)
               
   if args.scripts is not None:
      scripts = []
      for script in args.scripts:
         if script[0] == '(':
            scripts.append(literal_eval(script))
         else:
            ext = script[script.rfind('.')+1:]
            if ext in known_types:
               info = known_types[ext]
               scripts.append((info[1],script))
            else :
               raise ValueError('Unknown extension: '+ext)
   
   headings = toc(ast,args.autonumber,args.autonumbertitle) if args.toc else None
   
   renderer = HTML5Renderer()
   title = findTitle(ast)
   o.write('<html>\n')
   o.write('<head>\n')
   o.write('<title>{0}</title>\n'.format(title))

   o.write(prolog)
   
   for link in links:
      if args.inline:
         o.write('<link rel="{0}" type="{1}" href="{2}">\n'.format(link[0],link[1],dataURI(link[1],link[2])))
      else:
         o.write('<link rel="{0}" type="{1}" href="{2}">\n'.format(*link))
         
   for script in scripts:
      if args.inline:
         o.write('<script type="{0}" src="{1}"></script>\n'.format(link[0],dataURI(link[0],link[1])))
      else:
         o.write('<script type="{0}" src="{1}"></script>\n'.format(*script))
         
   o.write('</head>\n')
   o.write('<body>\n')
   o.write('<main>\n')
   
   o.write('<h1>{0}</h1>'.format(title))
   
   if headings is not None:
      o.write('<header class="toc">\n')
      o.write('<h1>Table of Contents</h1>\n')
      writeTOC(o,headings if len(headings)>1 or args.autonumbertitle else headings[0][2],args.autonumber)   
      o.write('</header>\n')
      
   o.write('<article>\n')
   o.write(renderer.render(ast))
   o.write('</article>\n')
   o.write('</main>\n')
   o.write('</body>\n')
   o.write('</html>\n')

if __name__ == '__main__':
   main()
