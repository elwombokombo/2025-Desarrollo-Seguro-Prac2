import { Router } from 'express';
import routes from '../controllers/authController';

const router = Router();

// healthcheck
router.get('/', routes.ping);

// auth
router.post('/login', routes.login);
router.post('/forgot-password', routes.forgotPassword);
router.post('/reset-password', routes.resetPassword);
router.post('/set-password', routes.setPassword);

// users
router.post('/users', routes.createUser);
router.put('/users/:id', routes.updateUser);

export default router;
