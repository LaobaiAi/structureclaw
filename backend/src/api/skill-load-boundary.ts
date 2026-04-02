import type { FastifyInstance } from 'fastify';
import { LoadBoundaryExecutionService } from '../services/load-boundary-execution.js';
import type { LoadBoundaryExecutionInput } from '../agent-skills/load-boundary/types.js';

export async function loadBoundaryRoutes(fastify: FastifyInstance) {
  const service = new LoadBoundaryExecutionService();

  // List all load-boundary skills
  fastify.get('/api/v1/skills/load-boundary', async (request, reply) => {
    try {
      const result = await service.listSkills();
      return reply.send(result);
    } catch (error) {
      fastify.log.error(error);
      return reply.status(500).send({ error: 'Failed to list load-boundary skills' });
    }
  });

  // Get specific skill by ID
  fastify.get('/api/v1/skills/load-boundary/:skillId', async (request, reply) => {
    try {
      const { skillId } = request.params as { skillId: string };
      const result = await service.getSkill(skillId);
      if (!result) {
        return reply.status(404).send({ error: `Skill not found: ${skillId}` });
      }
      return reply.send(result);
    } catch (error) {
      fastify.log.error(error);
      return reply.status(500).send({ error: 'Failed to get load-boundary skill' });
    }
  });

  // Execute a load-boundary skill
  fastify.post('/api/v1/skills/load-boundary/:skillId/execute', async (request, reply) => {
    try {
      const { skillId } = request.params as { skillId: string };
      const params = request.body as Record<string, unknown>;

      const input: LoadBoundaryExecutionInput = {
        skillId: skillId as any,
        action: 'execute',
        params,
      };

      const result = await service.execute(input);

      if (result.status === 'error') {
        return reply.status(400).send({ error: result.error });
      }

      return reply.send(result);
    } catch (error) {
      fastify.log.error(error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      return reply.status(500).send({ error: `Load-boundary execution failed: ${errorMessage}` });
    }
  });

  // Health check for load-boundary skills
  fastify.get('/api/v1/skills/load-boundary/health', async (request, reply) => {
    try {
      const { listBuiltinLoadBoundarySkills } = await import('../agent-skills/load-boundary/entry.js');
      const skills = listBuiltinLoadBoundarySkills();
      return reply.send({
        status: 'ok',
        count: skills.length,
        skills: skills.map((s) => s.id),
      });
    } catch (error) {
      fastify.log.error(error);
      return reply.status(503).send({ status: 'error', error: 'Load-boundary service unavailable' });
    }
  });
}
