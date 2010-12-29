<%page args="qa_list, layouts, prefix=''" />

<%doc>
    Generates one or more <tr> elements.
</%doc>

%for q, a in qa_list:
  %if q.is_repeatable():  
    <%include file="repeatable_question.tpl" args="q=q, a=a, layouts=layouts, prefix=prefix" />
  %else:
    <%include file="single_question.tpl" args="q=q, a=a, layouts=layouts, prefix=prefix" />
  %endif  
%endfor
