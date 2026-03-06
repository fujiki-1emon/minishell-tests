#include "lexer.h"

int	lex_quote(char const* line, int* i)
{
	char*	start;
	char*	end;

	start = &line[*i + 1];
	while (line[*i] == '\'' || line[*i] == '"')
	{
		if (line[*i] == (char)0)
			return (1);
		++i;
	}
	end = &line[*i];
	word = ft_strndup(start, end);
	push_tok(out, new_tok(TOK_WORD, word));
	return (0);
}

int	lex_word_end(char const* line, int* i)
{

	while (line[*i])
	{
		if (line[*i] == '\'' || line[*i] == '"')
			lex_quote(line, i);
	}
}

whitespace
meta characters
regular word
quoted word