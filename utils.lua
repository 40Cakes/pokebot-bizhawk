local utils = {}

function utils.translatePath(path)
	local separator = package.config:sub(1, 1)
	local pathTranslated = string.gsub(path, "\\", separator)
	return pathTranslated == nil and path or pathTranslated
end

return utils
