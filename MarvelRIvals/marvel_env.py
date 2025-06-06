# marvel_env.py
import gymnasium as gym
import msgpack, numpy as np
from sharedmem import RingBuffer

class MarvelRivalsEnv(gym.Env):
    observation_space = gym.spaces.Box(low=0, high=1, shape=(12, 13), dtype=np.float32)
    action_space      = gym.spaces.Box(low=-1, high=1, shape=(10,), dtype=np.float32)

    def reset(self, seed=None, options=None):
        # send "reset" flag; wait for fresh state
        RingBuffer.push("action", msgpack.pack({"reset": True}))
        state = msgpack.unpackb(RingBuffer.pop("state"))
        return self._state_to_obs(state), {}

    def step(self, action):
        RingBuffer.push("action", msgpack.pack({"vec": action.tolist()}))
        state = msgpack.unpackb(RingBuffer.pop("state"))
        obs   = self._state_to_obs(state)
        reward = self._compute_reward(state)
        done   = state["objectiveTicks"] >= 3600  # end of match
        return obs, reward, done, False, {}

    def _state_to_obs(self, s):
        hp      = np.array(s["heroHP"])/2500
        pos     = np.array(s["pos"])/50
        cd      = np.array(s["cooldown"])/10
        return np.concatenate([hp, pos.reshape(-1), cd.reshape(-1)])

    def _compute_reward(self, s):
        dmg = (2500 - np.mean(s["heroHP"])) / 2500
        obj = s["objectiveTicks"]/3600
        return 0.6*dmg + 0.4*obj
