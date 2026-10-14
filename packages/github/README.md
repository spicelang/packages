# github

Client for the [GitHub REST API](https://docs.github.com/rest), written in Spice and built on `std/net/http-client` and
`std/text/json`.

## Installation

```toml
[dependencies]
github = "^0.1.0"
```

```spice
import "std/data/vector";
import "spice_packages/github/github";
```

## Quick start

```spice
import "std/data/vector";
import "spice_packages/github/github";

f<int> main() {
    GitHubClient gh = GitHubClient();
    gh.loadTokenFromEnv(); // GITHUB_TOKEN or GH_TOKEN, optional for public data

    Result<Repository> repoResult = gh.getRepository("spicelang", "spice");
    if repoResult.isErr() {
        const String error = gh.lastError.describe();
        printf("Request failed: %s\n", error.getRaw());
        return 1;
    }
    const Repository& repo = repoResult.unwrap();
    printf("%s has %d stars\n", repo.fullName.getRaw(), repo.stargazersCount);
}
```

## Client configuration

| Method / field                     | Purpose                                                                   |
|------------------------------------|---------------------------------------------------------------------------|
| `GitHubClient(token)`              | Create a client, optionally with a personal access, App or OAuth token    |
| `setToken(token)`                  | Set or replace the token                                                  |
| `loadTokenFromEnv()`               | Read the token from `GITHUB_TOKEN`, falling back to `GH_TOKEN`            |
| `setBaseUrl(url)`                  | Use GitHub Enterprise Server, e.g. `https://github.example.com/api/v3`    |
| `setUserAgent(name)`               | Identify your application (GitHub asks for this)                          |
| `setTimeout(millis)`               | Read/write timeout of the connection                                      |
| `perPage`                          | Page size of listings (default 30, max 100)                               |
| `rateLimit`                        | Quota as of the last answer (`limit`, `remaining`, `used`, `reset`)       |
| `lastPageLinks`                    | `next`, `prev`, `first` and `last` page of the last listing, 0 if none    |
| `lastError`                        | Status, message, documentation URL and validation details of the last failure |

## Endpoints

| Area          | Methods |
|---------------|---------|
| Users         | `getAuthenticatedUser`, `getUser`, `getOrganization`, `getRateLimit` |
| Repositories  | `getRepository`, `listMyRepositories`, `listUserRepositories`, `listOrgRepositories`, `createRepository`, `deleteRepository`, `forkRepository`, `starRepository`, `unstarRepository`, `listTopics`, `listContributors`, `listBranches`, `getBranch`, `listTags` |
| Commits       | `listCommits`, `getCommit` |
| Contents      | `getFile`, `getReadme`, `listDirectory`, `createOrUpdateFile`, `deleteFile` |
| Issues        | `listIssues`, `getIssue`, `createIssue`, `updateIssue`, `closeIssue`, `reopenIssue`, `listComments`, `createComment`, `updateComment`, `deleteComment`, `listLabels`, `createLabel`, `addLabels`, `removeLabel` |
| Pull requests | `listPullRequests`, `getPullRequest`, `createPullRequest`, `updatePullRequest`, `mergePullRequest`, `listPullRequestFiles`, `listPullRequestCommits`, `listReviews`, `createReview`, `requestReviewers` |
| Releases      | `listReleases`, `getRelease`, `getLatestRelease`, `getReleaseByTag`, `createRelease`, `deleteRelease` |
| Actions       | `listWorkflows`, `listWorkflowRuns`, `getWorkflowRun`, `dispatchWorkflow`, `cancelWorkflowRun`, `rerunWorkflowRun` |
| Search        | `searchRepositories`, `searchIssues`, `searchUsers` |

Every method returns a `Result`. Resources (`Repository`, `Issue`, `PullRequest`, `Release`, ...) are plain structs with
camelCase fields. Values GitHub leaves out or sends as `null` are empty strings, `0` or `false`, and timestamps are ISO 8601
strings.

Write requests take input structs, such as `NewRepository`, `IssueChange`, `NewPullRequest`, `MergeOptions`, `NewRelease`,
`FileChange` or `WorkflowDispatch`. List filters (`IssueFilter`, `PullRequestFilter`, `CommitFilter`, `RepositoryFilter`,
`WorkflowRunFilter`, `SearchOptions`) are optional, and every listing has an overload without one. Empty fields are not
sent, so an update only changes what you set:

```spice
IssueChange issue;
issue.title = String("Crash when compiling generics");
issue.body = String("Steps to reproduce: ...");
issue.labels.pushBack(String("bug"));
Result<Issue> created = gh.createIssue("owner", "repo", issue);

FileChange change;
change.message = String("Update docs");
change.content = String("# Hello\n"); // Raw content, the client Base64-encodes it
change.sha = String("<blob sha of the current file>"); // Leave empty to create a new file
Result<FileCommit> commit = gh.createOrUpdateFile("owner", "repo", "docs/index.md", change);
```

## Errors

If GitHub answers with a non-2xx status, the `Error` code is that status (e.g. `404`) and the message is the reason phrase.
If no usable answer arrives (network failure, invalid JSON), the code is `ErrorCode::RuntimeError`. GitHub's full message
and any validation details stay in `gh.lastError` until the next request:

```spice
Result<Issue> issueResult = gh.createIssue("owner", "repo", "");
if issueResult.isErr() {
    const Error& error = issueResult.getErr();
    const String details = gh.lastError.describe(); // e.g. "422 Validation Failed (title: missing_field)"
    printf("%d: %s\n", error.getCode(), details.getRaw());
}
```

## Pagination

Listings return a single page. Pass the page number as the last argument and use `lastPageLinks` to keep going:

```spice
gh.perPage = 100l;
long page = 1l;
while page != 0l {
    Result<Vector<Issue>> issues = gh.listIssues("spicelang", "spice", page);
    if issues.isErr() { break; }
    // ... use issues.unwrap()
    page = gh.lastPageLinks.next;
}
```

## Other endpoints

For endpoints without a dedicated method, use the raw request methods. They take a path below the API root (or an
absolute URL) and a JSON body. Import `std/net/http` for `HttpMethod`.

- `request(method, path, body)` returns the `HttpResponse` whatever its status.
- `requestObject<T>` and `requestList<T>` decode the answer into any struct with a `loadJson(JsonValue*)` method.
- `requestInto<T>` fills an existing value, which is needed for generic resources like `SearchResult<T>`.
- `requestNoContent` is for endpoints that answer without data.

```spice
Result<Vector<Repository>> forks =
    gh.requestList<Repository>(HttpMethod::GET, String("/repos/spicelang/spice/forks"), String());
```

## Limitations

- Release asset uploads, GraphQL and webhooks are not supported.
- File contents above 1 MB are not delivered by the contents API. Fetch them from `Content.downloadUrl` instead.
- Each request opens its own connection, because `std/net/http-client` does not keep connections alive.
