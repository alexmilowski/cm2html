import io,base64
from CommonMark.node import Node

def text(n):
   sb = io.StringIO()
   for node,entering in n.walker():
      if node.t == 'text':
         sb.write(node.literal)
   text = sb.getvalue()
   sb.close()
   return text
   
def findTitle(ast):
   n = ast.first_child
   title = None
   while title is None and n is not None:
      if n.t == 'heading':
         title = text(n)
      n = n.nxt
   return title if title is not None else ""
   
def toc(ast,autonumber):
   top = [];
   current = [top];
   level = 0
   for node,entering in ast.walker():
      if node.t == 'heading' and entering:
         title = text(node)
         attrs = {}
         if node.level == level:
            current.pop()
            spec = (node.level,title,[],attrs)
            current[-1].append(spec)
            current.append(spec[2])
         elif node.level > level:
            # Added empty intermediary levels
            for newLevel in range(level+1,node.level+1):
               spec = (newLevel,None if newLevel < node.level else title,[],None if newLevel < node.level else attrs)
               current[-1].append(spec)
               current.append(spec[2])
            level = node.level
         elif node.level < level:
            for oldLevel in range(node.level,level+1):
               current.pop()
            spec = (node.level,title,[],attrs)
            current[-1].append(spec)
            current.append(spec[2])
            level = node.level
         tumbler = list(map(lambda x:len(x),current[0:-1]))
         node.id = 'h' + ''.join(map(lambda n:'-'+str(n),tumbler))
         attrs['id'] = node.id
         attrs['tumbler'] = tumbler
         if autonumber:
            first = node.first_child
            node.first_child = Node('text',first.sourcepos)
            first.prv = node.first_child
            node.first_child.parent = node
            node.first_child.nxt = first
            node.first_child.literal = ''.join(map(lambda n:str(n)+'.',tumbler)) + ' '
            
   return top

def dataURI(contentType,uri):
   sb = io.StringIO()
   for line in open(uri):
      sb.write(line)
   encoded = base64.urlsafe_b64encode(bytes(sb.getvalue(),'utf-8')).decode('utf-8')
   sb.close()
   return 'data:'+contentType+';base64,'+encoded
   
def writeTOC(os,toc,autonumber):
   for item in toc:
      id = '#'+item[3]['id'] if item[3] is not None else ''
      number = ''.join(map(lambda n:str(n)+'.',item[3]['tumbler'])) + ' ' if autonumber and item[3] is not None else ''
      if len(item[2]) == 0:
         os.write(
            '<summary class="toc-{0}">{3}<a href="{2}">{1}</a></summary>\n'.format(
               item[0],
               item[1] if item[1] is not None else '',
               id,
               number))
      else:
         os.write(
            '<details open><summary class="toc-{0}">{3}<a href="{2}">{1}</a></summary>\n'.format(
               item[0],
               item[1] if item[1] is not None else '',
               id,
               number))
         writeTOC(os,item[2],autonumber)
         os.write('</details>\n')
