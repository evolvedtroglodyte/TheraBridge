/**
 * Utility types for common TypeScript patterns
 * Provides reusable type helpers for null handling, deep operations, and conditional types
 */

/**
 * Nullable<T> - Allows T or null
 * Useful for values that can be explicitly null
 *
 * @example
 * type MaybeString = Nullable<string>; // string | null
 */
export type Nullable<T> = T | null;

/**
 * Optional<T> - Allows T or undefined
 * Useful for optional properties or function parameters
 *
 * @example
 * type MaybeNumber = Optional<number>; // number | undefined
 */
export type Optional<T> = T | undefined;

/**
 * ArrayElement<T> - Extracts the element type from an array type
 * Useful for working with array elements without explicitly specifying element types
 *
 * @example
 * type Item = ArrayElement<string[]>; // string
 * type User = ArrayElement<User[]>; // User
 */
export type ArrayElement<T> = T extends (infer E)[] ? E : never;

/**
 * DeepPartial<T> - Makes all properties of T and nested objects optional
 * Recursively applies Partial to all nested objects
 *
 * @example
 * interface User {
 *   name: string;
 *   address: { street: string; city: string };
 * }
 * type PartialUser = DeepPartial<User>;
 * // { name?: string; address?: { street?: string; city?: string } }
 */
export type DeepPartial<T> = T extends object
  ? {
      [P in keyof T]?: DeepPartial<T[P]>;
    }
  : T;

/**
 * DeepReadonly<T> - Makes all properties of T and nested objects readonly
 * Recursively applies readonly to all nested objects
 *
 * @example
 * interface User {
 *   name: string;
 *   settings: { theme: string };
 * }
 * type ImmutableUser = DeepReadonly<User>;
 * // { readonly name: string; readonly settings: { readonly theme: string } }
 */
export type DeepReadonly<T> = T extends object
  ? {
      readonly [P in keyof T]: DeepReadonly<T[P]>;
    }
  : T;

/**
 * WithRequired<T, K> - Makes specific properties K required in type T
 * Useful when you need to enforce certain properties while keeping others optional
 *
 * @example
 * interface User { name?: string; email?: string; id?: string }
 * type UserWithId = WithRequired<User, 'id'>; // { name?: string; email?: string; id: string }
 */
export type WithRequired<T, K extends keyof T> = T & Required<Pick<T, K>>;

/**
 * WithOptional<T, K> - Makes specific properties K optional in type T
 * Useful when you need to make certain required properties optional
 *
 * @example
 * interface User { name: string; email: string; id: string }
 * type PartialUser = WithOptional<User, 'email'>; // { name: string; email?: string; id: string }
 */
export type WithOptional<T, K extends keyof T> = Omit<T, K> &
  Partial<Pick<T, K>>;

/**
 * Additional utility types for common patterns
 */

/**
 * Prettify<T> - Flattens union types and improves IDE display of complex types
 * Useful for displaying intersected types more clearly
 *
 * @example
 * type Combined = Prettify<{ a: string } & { b: number }>;
 * // Displays as { a: string; b: number } instead of intersection
 */
export type Prettify<T> = {
  [K in keyof T]: T[K];
} & {};

/**
 * ValueOf<T> - Extracts the value types from an object type
 * Useful for getting a union of all possible values in an object
 *
 * @example
 * type Config = { theme: 'light' | 'dark'; debug: boolean };
 * type ConfigValue = ValueOf<Config>; // 'light' | 'dark' | boolean
 */
export type ValueOf<T> = T[keyof T];

/**
 * KeyOf<T> - Extracts all keys from an object type as a union
 * Similar to keyof but returned as a union instead of a type
 *
 * @example
 * type User = { id: string; name: string };
 * type UserKeys = KeyOf<User>; // 'id' | 'name'
 */
export type KeyOf<T> = keyof T;

/**
 * Entries<T> - Creates a type for key-value pair entries of an object
 * Useful for iteration patterns
 *
 * @example
 * type User = { id: string; name: string };
 * type UserEntries = Entries<User>; // ['id' | 'name', string][]
 */
export type Entries<T> = Array<[KeyOf<T>, ValueOf<T>]>;

/**
 * Asyncify<T> - Wraps all function properties to return Promises
 * Useful for converting sync operations to async equivalents
 *
 * @example
 * type Sync = { getValue: () => string };
 * type Async = Asyncify<Sync>; // { getValue: () => Promise<string> }
 */
export type Asyncify<T> = {
  [K in keyof T]: T[K] extends (...args: infer A) => infer R
    ? (...args: A) => Promise<R>
    : T[K];
};

/**
 * Awaited<T> - Extracts the type from a Promise
 * Removes Promise wrapper to get the underlying type
 *
 * @example
 * type PromiseString = Promise<string>;
 * type Result = Awaited<PromiseString>; // string
 */
export type Awaited<T> = T extends Promise<infer U> ? U : T;

/**
 * NotNull<T> - Excludes null from a type
 * Similar to NonNullable but explicitly for null
 *
 * @example
 * type Nullable = string | null;
 * type NotNullable = NotNull<Nullable>; // string
 */
export type NotNull<T> = Exclude<T, null>;

/**
 * NotUndefined<T> - Excludes undefined from a type
 * Similar to NonNullable but explicitly for undefined
 *
 * @example
 * type Optional = string | undefined;
 * type Required = NotUndefined<Optional>; // string
 */
export type NotUndefined<T> = Exclude<T, undefined>;

/**
 * NoNullable<T> - Excludes both null and undefined from a type
 * Combines NotNull and NotUndefined
 *
 * @example
 * type Nullable = string | null | undefined;
 * type Required = NoNullable<Nullable>; // string
 */
export type NoNullable<T> = Exclude<T, null | undefined>;

/**
 * Subset<T, U> - Ensures T is a subset of U (all keys of T must exist in U with compatible types)
 * Useful for type-safe constrained generics
 *
 * @example
 * type Config = { a: string; b: number };
 * type SubConfig = Subset<{ a: string }, Config>; // Valid
 * type BadConfig = Subset<{ c: string }, Config>; // Error: 'c' not in Config
 */
export type Subset<T, U extends T> = U;

/**
 * UnionToIntersection<T> - Converts a union type to an intersection
 * Useful for combining multiple types
 *
 * @example
 * type Union = { a: string } | { b: number };
 * type Intersection = UnionToIntersection<Union>;
 * // { a: string } & { b: number }
 */
export type UnionToIntersection<T> = (
  T extends any ? (k: T) => void : never
) extends (k: infer I) => void
  ? I
  : never;

/**
 * StrictOmit<T, K> - Type-safe version of Omit that requires keys to exist in T
 * Prevents accidentally omitting non-existent keys
 *
 * @example
 * type User = { id: string; name: string };
 * type NoId = StrictOmit<User, 'id'>; // Valid
 * type BadOmit = StrictOmit<User, 'missing'>; // Error: 'missing' not in User
 */
export type StrictOmit<T, K extends keyof T> = Omit<T, K>;

/**
 * StrictPick<T, K> - Type-safe version of Pick that requires keys to exist in T
 * Prevents accidentally picking non-existent keys
 *
 * @example
 * type User = { id: string; name: string };
 * type IdOnly = StrictPick<User, 'id'>; // Valid
 * type BadPick = StrictPick<User, 'missing'>; // Error: 'missing' not in User
 */
export type StrictPick<T, K extends keyof T> = Pick<T, K>;

/**
 * Mutable<T> - Removes readonly modifiers from all properties
 * Inverse of DeepReadonly
 *
 * @example
 * type ReadonlyUser = { readonly name: string };
 * type MutableUser = Mutable<ReadonlyUser>; // { name: string }
 */
export type Mutable<T> = {
  -readonly [K in keyof T]: T[K];
};

/**
 * DeepMutable<T> - Recursively removes readonly modifiers from nested properties
 *
 * @example
 * type ReadonlyNested = { readonly user: { readonly name: string } };
 * type Mutable = DeepMutable<ReadonlyNested>;
 * // { user: { name: string } }
 */
export type DeepMutable<T> = T extends object
  ? {
      -readonly [K in keyof T]: DeepMutable<T[K]>;
    }
  : T;
