import express, { Request, Response, NextFunction } from "express";
import session from "express-session";

declare module "express-session" {
  interface SessionData {
    user?: {
      id: number;
      username: string;
      role: string;
    };
  }
}

const app = express();
const PORT = 8005;

const SESSION_SECRET = process.env.SESSION_SECRET ?? "changeme-session-secret";

app.use(express.json());

app.use(
  session({
    secret: SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
    cookie: {
      httpOnly: true,
      secure: false,
      maxAge: 24 * 60 * 60 * 1000,
    },
  })
);

const VALID_USER = {
  id: 1,
  username: "admin",
  password: "admin123",
  role: "admin",
};

function requireAuth(req: Request, res: Response, next: NextFunction): void {
  if (!req.session.user) {
    res.status(401).json({ error: "Unauthorized" });
    return;
  }
  next();
}

app.post("/login", (req: Request, res: Response): void => {
  const { username, password } = req.body;

  if (!username || !password) {
    res.status(400).json({ error: "Username and password are required" });
    return;
  }

  if (username !== VALID_USER.username || password !== VALID_USER.password) {
    res.status(401).json({ error: "Invalid credentials" });
    return;
  }

  req.session.user = {
    id: VALID_USER.id,
    username: VALID_USER.username,
    role: VALID_USER.role,
  };

  res.status(200).json({ message: "Login successful" });
});

app.get("/profile", requireAuth, (req: Request, res: Response): void => {
  res.status(200).json({ user: req.session.user });
});

app.post("/logout", requireAuth, (req: Request, res: Response): void => {
  req.session.destroy((err) => {
    if (err) {
      res.status(500).json({ error: "Failed to logout" });
      return;
    }
    res.clearCookie("connect.sid");
    res.status(200).json({ message: "Logout successful" });
  });
});

app.get("/admin", requireAuth, (req: Request, res: Response): void => {
  res.status(200).json({
    message: `Welcome, administrator ${req.session.user!.username}!`,
  });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
