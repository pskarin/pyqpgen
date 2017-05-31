function str = mat2str_c(M)

if issparse(M)
    str = mat2str(full(M),15);
else
    str = mat2str(M,15);
end

len = length(str);
if len == 1
  str = strcat('{', str, '}');
end

for jj = 1:len
    if isequal(str(jj),'[')
        str(jj)  = '{';
    end
    if isequal(str(jj),' ')
        str(jj) = ',';
    end
    if isequal(str(jj),';')
        str(jj) = ',';
    end
    if isequal(str(jj),']')
        str(jj) = '}';
    end
end
