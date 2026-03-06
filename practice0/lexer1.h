/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   lexer1.h                                           :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: stanizak <marvin@42.fr>                    +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/03/01 19:33:29 by stanizak          #+#    #+#             */
/*   Updated: 2026/03/01 19:33:31 by stanizak         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#ifndef LEXER1_H
# define LEXER1_H

# include <stdio.h>
# include <stdlib.h>
# include <string.h>
# include <readline/history.h>
# include <readline/readline.h>

typedef enum e_token_type
{
	T_WORD,
	T_PIPE,
	T_REDIRECT_IN,
	T_REDIRECT_OUT,
	T_REDIRECT_APPEND,
	T_HEREDOC
}	t_token_type;

typedef struct s_token
{
	t_token_type	type;
	char			*value;
	struct s_token	*next;
}	t_token;

t_token	*new_tok(t_token_type type, char *value);
int		push_tok(t_token **list, t_token *token);
int		lex_word_end(char const *line, int *i);
int		lex_line(char const *line, t_token **out);

#endif
