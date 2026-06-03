// Plugins de segurança:
//   - eslint-plugin-security      -> regras gerais de segurança em Node
//   - eslint-plugin-no-unsanitized-> bloqueia uso direto de innerHTML etc.
//   - @typescript-eslint          -> parser/regras de TS
//
// Documentação: https://github.com/eslint-community/eslint-plugin-security

module.exports = {
    root: true,
    env: {
        node: true,
        browser: true,
        es2022: true,
    },
    parserOptions: {
        ecmaVersion: 2022,
        sourceType: "module",
    },
    plugins: [
        "security",
        "no-unsanitized",
    ],
    extends: [
        "eslint:recommended",
        "plugin:security/recommended-legacy",
        "plugin:no-unsanitized/recommended-legacy",
    ],
    overrides: [
        {
            files: ["*.ts", "*.tsx"],
            parser: "@typescript-eslint/parser",
            plugins: ["@typescript-eslint", "security", "no-unsanitized"],
            extends: [
                "eslint:recommended",
                "plugin:@typescript-eslint/recommended",
                "plugin:security/recommended-legacy",
                "plugin:no-unsanitized/recommended-legacy",
            ],
        },
    ],
    rules: {
        "security/detect-object-injection": "error",
        "security/detect-non-literal-fs-filename": "error",
        "security/detect-non-literal-regexp": "error",
        "security/detect-unsafe-regex": "error",
        "security/detect-buffer-noassert": "error",
        "security/detect-child-process": "error",
        "security/detect-disable-mustache-escape": "error",
        "security/detect-eval-with-expression": "error",
        "security/detect-no-csrf-before-method-override": "error",
        "security/detect-possible-timing-attacks": "error",
        "security/detect-pseudoRandomBytes": "error",
        // warnings de estilo
        "no-unused-vars": "off",
        "@typescript-eslint/no-unused-vars": "off",
        "@typescript-eslint/no-explicit-any": "off",
    },
    ignorePatterns: [
        "node_modules/",
        "dist/",
        "build/",
        "*.min.js",
    ],
};
