/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   lexer.c                                            :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: stanizak <stanizak@student.42tokyo.jp>     +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/01/01 00:00:00 by claude            #+#    #+#             */
/*   Updated: 2026/03/01 21:17:19 by stanizak         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "../core/ms.h"

static t_token	*new_tok(t_shell *sh, t_tok_type type, char *v)
{
	t_token	*t;

	t = ms_alloc(&sh->mem, sizeof(*t));
	if (!t)
		return (NULL);
	t->type = type;
	t->value = v;
	t->next = NULL;
	return (t);
}

static int	push_tok(t_token **lst, t_token *tok)
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

static int	lex_op(t_shell *sh, const char *s, int *i, t_token **out)
{
	t_tok_type	type;

	type = TOK_PIPE;
	if (s[*i] == '<' && s[*i + 1] == '<')
		type = TOK_HEREDOC;
	else if (s[*i] == '>' && s[*i + 1] == '>')
		type = TOK_REDIRECT_APPEND;
	else if (s[*i] == '<')
		type = TOK_REDIRECT_IN;
	else if (s[*i] == '>')
		type = TOK_REDIRECT_OUT;
	if (type == TOK_HEREDOC || type == TOK_REDIRECT_APPEND)
		*i += 2;
	else
		*i += 1;
	return (push_tok(out, new_tok(sh, type, NULL)));
}

static int	syntax_error_quote(t_shell *sh, char quote)
{
	ms_err("minishell: unexpected EOF while looking for matching `");
	write(2, &quote, 1);
	ms_err("'\n");
	ms_err("minishell: syntax error: unexpected end of file\n");
	sh->exit_code = 2;
	return (1);
}

int	lex_line(t_shell *sh, const char *line, t_token **out)
{
	int		st;
	int		i;
	int		q;
	char	*word;

	i = 0;
	*out = NULL;
	while (line[i])
	{
		while (line[i] && ft_isspace(line[i]))
			i++;
		if (!line[i])
			break ;
		if (ft_strchr("|<>", line[i]))
			lex_op(sh, line, &i, out);
		else
		{
			st = i;
			q = lex_word_end(line, &i);
			if (q != 0)
				return (syntax_error_quote(sh, (char)q));
			word = ms_strndup(&sh->mem, line + st, i - st);
			push_tok(out, new_tok(sh, TOK_WORD, word));
		}
	}
	return (0);
unsigned}
