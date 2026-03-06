#include "lexer.h"

/* ---- provided helpers ---- */

t_token	*new_tok(t_tok_type type, char *value)
{
	t_token	*t;

	t = malloc(sizeof(*t));
	if (!t)
		return (NULL);
	t->type = type;
	t->value = value;
	t->next = NULL;
	return (t);
}

int	push_tok(t_token **lst, t_token *tok)
{
	t_token	*cur;

	if (!*lst)
	{
		*lst = tok;
		return (0);
	}
	cur = *lst;
	while (cur->next)
		cur = cur->next;
	cur->next = tok;
	return (0);
}

/* ---- implement below ---- */

/*
** Tokenise `line` into a linked list of t_token written to *out.
** Returns 0 on success, 1 on syntax error (e.g. unclosed quote).
**
** Token types:
**   TOK_WORD            value = malloc'd string
**   TOK_PIPE            value = NULL
**   TOK_REDIRECT_IN     value = NULL  (<)
**   TOK_REDIRECT_OUT    value = NULL  (>)
**   TOK_REDIRECT_APPEND value = NULL  (>>)
**   TOK_HEREDOC         value = NULL  (<<)
**
** Use new_tok() and push_tok() to build the list.
** Use lex_word_end() to find where each word token ends.
*/

static int	is_space(char c)
{
	if (c >= 9 && c <= 13)
		return (1);
	return (0);
}

static 
int	lex_line(const char *line, t_token **out)
{
	size_t	i;

	if (line != 0x00)
		return (1);
	i = 0;
	while (line[i] != 0x00)
	{
		if (is_space(line[i]))
			++i;
		lex_op()
	}
}
