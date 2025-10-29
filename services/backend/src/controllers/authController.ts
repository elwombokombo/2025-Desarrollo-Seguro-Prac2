import { Request, Response, NextFunction } from 'express';
import AuthService from '../services/authService';
import { User } from '../types/user';

const ping = async (req: Request, res: Response, next: NextFunction) => {
  try {
    res.json({ msg: 'ok' });
  } catch (err) {
    next(err);
  }
};

const login = async (req: Request, res: Response, next: NextFunction) => {
  const { username, password } = req.body;
  try {
    const user = await AuthService.authenticate(username, password);
    const token = await AuthService.generateJwt(user.id);
    res.json({ token, user });
  } catch (err) {
    next(err);
  }
};

const forgotPassword = async (req: Request, res: Response, next: NextFunction) => {
  const { email } = req.body;
  try {
    await AuthService.sendResetPasswordEmail(email);
    res.sendStatus(204);
  } catch (err) {
    next(err);
  }
};

const resetPassword = async (req: Request, res: Response, next: NextFunction) => {
  const { token, newPassword } = req.body;
  try {
    await AuthService.resetPassword(token, newPassword);
    res.sendStatus(204);
  } catch (err) {
    next(err);
  }
};

const setPassword = async (req: Request, res: Response, next: NextFunction) => {
  const { token, newPassword } = req.body;
  try {
    await AuthService.setPassword(token, newPassword);
    res.sendStatus(204);
  } catch (err) {
    next(err);
  }
};

const createUser = async (req: Request, res: Response, next: NextFunction) => {
  const { username, password, email, first_name, last_name } = req.body;
  try {
    const user: User = {
      username,
      password,
      email,
      first_name,
      last_name,
    };

    const userDB = await AuthService.createUser(user); // 👈 aquí AuthService debe hashear
    res.status(201).json(userDB);
  } catch (err) {
    next(err);
  }
};

const updateUser = async (req: Request, res: Response, next: NextFunction) => {
  const userId = parseInt(req.params.id, 10);
  const { username, password, email, first_name, last_name } = req.body;

  try {
    const user: User = {
      id: userId, // 👈 se agrega el id
      username,
      password,
      email,
      first_name,
      last_name,
    };

    const userDB = await AuthService.updateUser(user); // 👈 AuthService debe hashear si cambia la pass
    res.status(200).json(userDB);
  } catch (err) {
    next(err);
  }
};

export default {
  ping,
  login,
  forgotPassword,
  resetPassword,
  setPassword,
  createUser,
  updateUser,
};
