/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   lexer_word.c                                       :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: stanizak <stanizak@student.42tokyo.jp>     +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/01/01 00:00:00 by claude            #+#    #+#             */
/*   Updated: 2026/03/01 20:56:23 by stanizak         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "../core/ms.h"

int	lex_word_end(const char *line, int *i)
{
	char	q;

	q = 0;
	while (line[*i])
	{
		if (!q && ft_isspace(line[*i]))
			break ;
		if (!q && ft_strchr("|<>", line[*i]))
			break ;
		if (!q && (line[*i] == '\'' || line[*i] == '"'))
			q = line[*i];
		else if (q && line[*i] == q)
			q = 0;
		(*i)++;
	}
	return ((unsigned char)q);
}
/*
先読みしないことが軸解析では大事*/