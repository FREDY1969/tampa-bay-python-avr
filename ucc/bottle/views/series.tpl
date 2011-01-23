<%!
    def has_rows(q, a):
        return True
%>


<%def name="rows(q, a, layouts, prefix, suffix='')">
  <%include file="question_list.tpl" args="qa_list=q.gen_subquestions(a), layouts=layouts, prefix='{}{}{}.'.format(prefix, q.name, suffix)" />
</%def>
