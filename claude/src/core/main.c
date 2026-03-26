/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   main.c                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: claude <claude@student.42.fr>              +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/01/01 00:00:00 by claude            #+#    #+#             */
/*   Updated: 2026/01/01 00:00:00 by claude           ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "ms.h"

#ifndef ECHOCTL
# define ECHOCTL 0
#endif

volatile sig_atomic_t	g_sig;

void	ms_term_disable_echoctl(t_shell *sh)
{
	struct termios	term;

	if (!sh->interactive)
		return ;
	if (tcgetattr(STDIN_FILENO, &term) != 0)
		return ;
	term.c_lflag &= ~ECHOCTL;
	tcsetattr(STDIN_FILENO, TCSANOW, &term);
}

static void	restore_terminal(t_shell *sh)
{
	if (!sh->interactive || !sh->term_saved)
		return ;
	tcsetattr(STDIN_FILENO, TCSANOW, &sh->term_orig);
}

static int	init_shell(t_shell *sh, char **envp)
{
	rl_catch_signals = 0;
	sh->exit_code = 0;
	sh->interactive = isatty(STDIN_FILENO);
	sh->term_saved = false;
	if (env_init(&sh->env, envp) != 0)
		return (1);
	if (sh->interactive)
	{
		if (tcgetattr(STDIN_FILENO, &sh->term_orig) == 0)
			sh->term_saved = true;
		ms_term_disable_echoctl(sh);
	}
	return (0);
}

int	main(int argc, char **argv, char **envp)
{
	t_shell	sh;

	(void)argc;
	(void)argv;
	if (init_shell(&sh, envp) != 0)
		return (1);
	ms_loop(&sh);
	restore_terminal(&sh);
	clear_history();
	env_free(&sh.env);
	return (sh.exit_code);
}
