# Putting the corpus on GitHub

This repository is the **public scholarly artifact**: the TEI, the data files behind it, and the method
notes. It is what you point a professor, a librarian or a journal at.

It is not the site. The site's source lives in `Poetry Analysis/`, in its own repository, and that one
stays private. Keeping them apart is deliberate: the corpus is meant to be examined and reused, the
application is not.

## What people can and cannot do with it

Worth knowing before you publish, because "public" is not one thing.

The poems themselves are public domain and always were. Nobody needs your permission for those, and
nothing here claims otherwise.

Everything Laurel *added* — the per-line scansion, the rhyme lettering, the metre determinations, the
canonical references, the permanent identifiers, the audio timings, the TEI encoding, the selection and
arrangement — is under **CC BY-SA 4.0**. So someone may copy it, adapt it, and use it commercially, but
they must credit Laurel and license what they build under the same terms. They cannot fold it into a
closed product and keep it closed.

That is the trade. A licence that forbade reuse outright would also disqualify the corpus from being
cited or built on, which is the entire reason to publish it. What ShareAlike prevents is the case you
were actually worried about: someone taking the work, closing it, and passing it off as theirs.

## Publishing it

**1. Create an empty repository on GitHub.**

Go to [github.com/new](https://github.com/new).

- Repository name: `laurel-corpus`
- Public
- **Do not** tick "Add a README", "Add .gitignore" or "Choose a license" — this repository already has
  all three, and an initialised repository will refuse the first push.

**2. Get a token to push with.** GitHub stopped accepting account passwords over HTTPS. Go to
[github.com/settings/tokens](https://github.com/settings/tokens) → *Generate new token (classic)* →
tick **repo** → generate, and copy it. You paste it when git asks for a *password*. It is shown once.

**3. Push.** In Terminal:

    cd ~/Contubernales/laurel-corpus
    ./publish.sh <your-github-username>

That fills the real address into `CITATION.cff`, adds the remote and pushes. About 40 MB; a minute or
two. When it finishes the repository is live.

## Worth doing once it is up

**Add a DOI.** [Zenodo](https://zenodo.org) gives a dataset a permanent citable identifier. Sign in with
GitHub, switch this repository on in Zenodo's GitHub settings, then make a release on GitHub
(*Releases* → *Create a new release*, tag `v1.0`). Zenodo mints a DOI and archives that release. This is
what makes the corpus citable in a journal rather than merely linkable, and it is the single thing that
most raises how a researcher reads the work.

**Say what it is in the repository description.** One line, at the top right of the GitHub page:
*416 works of public domain English verse in TEI, with per-line scansion and canonical references.*

**Add topics**: `tei`, `digital-humanities`, `poetry`, `prosody`, `public-domain`.

## Keeping it current

The repository is generated, not maintained by hand. It had already drifted behind the working corpus
once — it was still shipping a Southey whose opening section was a modern publisher's cataloguing
record, days after that was fixed. So after any run of corrections to the texts:

    cd ~/Contubernales/laurel-corpus
    ./assemble.sh                    # rebuilds the TEI and copies the data, and prints the figures
    git add -A && git commit -m "Rebuild from the corpus"
    git push

`assemble.sh` prints the works, poems, lines and recordings it found. If those disagree with the numbers
in `README.md` and `CITATION.cff`, fix those two files in the same commit — a corpus that misstates its
own size is the first thing a sceptical reader will catch.

## The other repository

`Poetry Analysis/` is now under version control too, but it has no remote: the only copy is this laptop.
A private GitHub repository would be an off-machine backup of the pipeline, the site and — the part that
genuinely could not be reconstructed — the permanent-id registry and the audio alignments. Same steps as
above, but tick **Private** on the new-repository page. Nothing in it becomes visible to anyone.
