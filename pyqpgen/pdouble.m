function [] = pdouble(fid, name, data)
  fprintf(fid, '#define %s {', name);
  for i=1:size(data, 1)
    for j=1:size(data, 2)
      if i ~= 1 | j ~= 1
        fprintf(fid, ', ');
      end
      if data(i,j) == Inf
        fprintf(fid, 'DBL_MAX');
      elseif data(i,j) == -Inf
        fprintf(fid, 'DBL_MIN');
      else
        fprintf(fid, '%e', data(i,j));
      end
    end
  end
  fprintf(fid, '}\n');
  fprintf(fid, '#define %s_size %d\n', name, size(data,1)*size(data,2));
end
