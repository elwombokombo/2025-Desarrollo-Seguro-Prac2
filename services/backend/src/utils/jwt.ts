import jwt from 'jsonwebtoken';

const getSecret = (): string => {
const s = process.env.JWT_SECRET;
if (!s) {
  throw new Error('JWT_SECRET is not defined');
  return s;
};
};

const generateToken = (userId: string) => {
  return jwt.sign(
    { id: userId }, 
    getSecret(), 
    { expiresIn: '1h' }
  );
};

const verifyToken = (token: string) => {
  return jwt.verify(token, getSecret());
};

export default {
  generateToken,
  verifyToken
}