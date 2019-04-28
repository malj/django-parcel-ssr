# React with [TypeScript](https://www.typescriptlang.org/) example

Install dependencies

```bash
npm install typescript
```

Install required type declarations, for example for the default React setup:

```bash
npm install @types/react @types/react-dom @types/react-helmet @types/styled-jsx
```

Create a [`tsconfig.json`](https://www.typescriptlang.org/docs/handbook/tsconfig-json.html) file in your project root, as required by your project. For example:

```json
{
    "compilerOptions": {
        "target": "es5",
        "strict": true,
        "esModuleInterop": true,
        "jsx": "react"
    }
}
```

**Important**: Parcel 1.x uses `tsc` compiler for compiling TypeScript files, which means that Babel plugins such as `styled-jsx` do not work out of the box ([source](https://github.com/zeit/styled-jsx/issues/29)). Parcel 2.x will allow optional TypeScript compiling via Babel 7+ using `@babel/preset-typescript` ([source](https://github.com/parcel-bundler/parcel/issues/2023)), but for now a [3d party Parcel plugin](https://github.com/Banou26/parcel-plugin-babel-typescript) can be used. 

To use Babel plugins install the required dependencies:

```bash
npm install parcel-plugin-babel-typescript @babel/preset-typescript
```

Update your `.babelrc` presets afterwards:

```json
{
    "presets": [
        "@babel/preset-typescript"
    ],
    "plugins": [
        "styled-jsx/babel"
    ]
}
```

Make sure that your `tsconfig.json` is configured to leave JSX transformations to Babel:

```json
{
    "compilerOptions": {
        "jsx": "preserve"
    }
}
```


