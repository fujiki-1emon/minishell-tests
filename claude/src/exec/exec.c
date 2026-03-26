/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   exec.c                                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: claude <claude@student.42.fr>              +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/01/01 00:00:00 by claude            #+#    #+#             */
/*   Updated: 2026/01/01 00:00:00 by claude           ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "../core/ms.h"

static void	exec_not_found(t_shell *sh, t_cmd *cmd)
{
	char	*path;

	path = find_exec_path(sh, cmd->argv[0]);
	if (!path)
	{
		ms_err("minishell: ");
		ms_err(cmd->argv[0]);
		ms_err(": command not found\n");
		exit(127);
	}
	execve(path, cmd->argv, sh->env.arr);
	if (errno == ENOENT && ft_strchr(cmd->argv[0], '/'))
		exit(ms_perror(cmd->argv[0], NULL, 127));
	if (errno == ENOENT)
		exit(127);
	exit(ms_perror(cmd->argv[0], NULL, 126));
}

void	child_exec(t_shell *sh, t_cmd *cmd)
{
	int	ret;

	sig_set_exec_child();
	ret = apply_redirects(sh, cmd->redirects);
	if (ret != 0)
		exit(ret);
	ret = run_builtin(sh, cmd);
	if (ret >= 0)
		exit(ret);
	if (!cmd->argv || !cmd->argv[0])
		exit(0);
	if (!cmd->argv[0][0])
	{
		ms_err("minishell: : command not found\n");
		exit(127);
	}
	exec_not_found(sh, cmd);
}

static int	exec_single_parent(t_shell *sh, t_cmd *cmd)
{
	int	in_save;
	int	out_save;
	int	ret;

	in_save = dup(STDIN_FILENO);
	out_save = dup(STDOUT_FILENO);
	ret = apply_redirects(sh, cmd->redirects);
	if (ret == 0)
		ret = run_builtin(sh, cmd);
	dup2(in_save, STDIN_FILENO);
	dup2(out_save, STDOUT_FILENO);
	close(in_save);
	close(out_save);
	if (ret < 0)
		ret = 1;
	return (ret);
}

int	exec_pipeline(t_shell *sh, t_pipeline *pl)
{
	int	ret;

	sig_set_exec_parent();
	if (pl->count == 1 && is_parent_builtin(&pl->cmds[0]))
		ret = exec_single_parent(sh, &pl->cmds[0]);
	else if (pl->count == 1 && (!pl->cmds[0].argv || !pl->cmds[0].argv[0]))
		ret = apply_redirects(sh, pl->cmds[0].redirects);
	else
		ret = exec_forked_pipeline(sh, pl);
	if (g_sig == SIGINT)
	{
		write(STDERR_FILENO, "\n", 1);
		ret = 130;
	}
	sig_set_interactive();
	return (ret);
}
