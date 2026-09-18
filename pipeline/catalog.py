"""Corpus catalogue: resolve author + title queries against the Gutenberg catalogue CSV, download the texts,
parse them with generic.py, and write work JSON. Hand-parsed works in ingest.py are left alone.

    python3 catalog.py            # resolve, download (cached), parse, report
"""
import sys, csv, json, os, re, sys, urllib.request, collections
import generic
from generic import parse_gutenberg, meter_guess, meter_share, METER_FLOOR
from ingest import apply_corrections
from ingest import OUT, SRC

CAT = os.path.join(SRC, 'pg_catalog.csv')

# (slug, catalogue query, display title, blurb, published, form/meter hints)
# WARNING. A full run of this script rebuilds index.json from QUERIES, EPICS and ORIGINALS alone, which
# silently drops the 169 poets that pipeline/obev.py adds from the Oxford Book of English Verse. After any
# full re-parse, obev.py must be re-run before analyze.py, or the library loses those poets.
#     python3 catalog.py && python3 obev.py && python3 analyze.py && ...
# Passing slugs re-parses only those works and is safe.

QUERIES = [
    # ---- gap-fill, 11 Sep 2026 (ebook numbers given directly)
    # ---- the famous poems, 12 Sep 2026. pipeline/canon.py checks three hundred poems a reader is most
    # likely to come looking for against the real texts; a hundred were absent because we held the wrong
    # volume of the right poet. Each ebook below was fetched and the poem's first line confirmed in it
    # before the entry was written. Where a poet already has a book here, this is a second edition
    # alongside it, not a replacement, which is what a library holds anyway.
    ('dryden-poems', 11488, 'The Poetical Works, Volume I', "Dryden's own verse rather than his Virgil: Absalom and Achitophel, Mac Flecknoe, A Song for St Cecilia's Day, and the satires in heroic couplets.", '1660–1700', 'heroic couplets'),
    ('shelley-later-poems', 4798, 'The Complete Poetical Works, Volume II', 'Shelley from 1816 to 1819: "Ozymandias", the "Ode to the West Wind", "To a Skylark", "The Masque of Anarchy", "Julian and Maddalo".', '1816–1819', None),
    ('tennyson-early-poems', 8601, 'The Early Poems', 'Tennyson before the laureateship: "Ulysses", "The Lady of Shalott", "The Lotos-Eaters", "Mariana", "Break, break, break".', '1830–1842', None),
    ('yeats-poems', 38877, 'Poems', 'Yeats\'s early collected volume: "The Lake Isle of Innisfree", "When You Are Old", "The Song of Wandering Aengus", The Wanderings of Oisin.', '1895', None),
    ('carroll-looking-glass', 12, 'Through the Looking-Glass', 'The verse of Carroll\'s second Alice book: "Jabberwocky", "The Walrus and the Carpenter", the White Knight\'s song.', '1871', None),
    ('lear-nonsense-songs', 13647, 'Nonsense Songs', 'Lear beyond the limericks: "The Owl and the Pussy-Cat", "The Jumblies", "The Dong with a Luminous Nose".', '1871', None),
    ('longfellow-poems', 1365, 'The Complete Poetical Works', 'Longfellow\'s shorter poems: "Paul Revere\'s Ride", "A Psalm of Life", "The Wreck of the Hesperus", "The Village Blacksmith".', '1839–1882', None),
    ('kipling-verses', 323, 'Verses 1889–1896', 'Kipling\'s first collected verse: "Gunga Din", "Mandalay", "Danny Deever", "The Ballad of East and West".', '1889–1896', None),
    ('hardy-past-and-present', 3168, 'Poems of the Past and the Present', 'Hardy\'s second book of verse: "The Darkling Thrush", the Boer War poems, "The Souls of the Slain".', '1901', None),
    ('teasdale-flame-shadow', 591, 'Flame and Shadow', 'Sara Teasdale in 1920: "There Will Come Soft Rains", "Let It Be Forgotten", "Night Song at Amalfi".', '1920', None),
    ('mccrae-flanders', 353, 'In Flanders Fields, and Other Poems', 'John McCrae\'s war poems, with an essay by Sir Andrew Macphail.', '1919', None),
    ('de-la-mare-listeners', 22569, 'The Listeners and Other Poems', 'Walter de la Mare in 1912: "The Listeners", "Silver", "The Song of the Mad Prince".', '1912', None),
    ('chesterton-wild-knight', 12037, 'The Wild Knight and Other Poems', 'Chesterton\'s first book of verse: "The Donkey", "By the Babe Unborn", "A Certain Evening".', '1900', None),
    ('robinson-town-down-river', 76699, 'The Town Down the River', 'E. A. Robinson in 1910: "Miniver Cheevy", "For a Dead Lady", the Lincoln ode.', '1910', None),
    ('sassoon-war-poems', 45199, 'The War Poems', 'Sassoon\'s trench poems collected: "Everyone Sang", "The General", "Base Details", "Does It Matter?".', '1919', None),
    ('wordsworth-vol2', 12145, 'The Poetical Works, Volume II', 'Wordsworth\'s shorter poems: "I wandered lonely as a cloud", "Composed upon Westminster Bridge", "The world is too much with us", the Lucy poems.', '1798–1807', None),
    ('wordsworth-vol3', 12383, 'The Poetical Works, Volume III', 'Wordsworth continued: "The Solitary Reaper", the "Ode: Intimations of Immortality", the later sonnets.', '1802–1815', None),
    ('shelley-poems', 4797, 'The Complete Poetical Works, Volume I', 'Shelley: Queen Mab, Alastor, Prometheus Unbound, and the lyrics to 1820, in the Hutchinson text.', '1813–1820', None),
    ('coleridge-poems', 8208, 'Poems of Coleridge', 'Kubla Khan, Christabel, Frost at Midnight, Dejection and the conversation poems.', '1796–1817', None),
    ('keats-endymion', 24280, 'Endymion: A Poetic Romance', 'Keats\'s four-book romance in couplets, "A thing of beauty is a joy for ever".', '1818', 'heroic couplets'),
    ('keats-1817', 8209, 'Poems (1817)', 'Keats\'s first book: "On First Looking into Chapman\'s Homer", "Sleep and Poetry", the early sonnets.', '1817', None),
    ('goldsmith-poems', 3545, 'Poems', 'The Traveller, The Deserted Village, Retaliation and the lighter pieces: Goldsmith\'s elegy for a depopulated countryside and the rest of his verse, in heroic couplets and ballad measures.', '1764–1774', None),
    ('holmes-poems', 7388, 'Poetical Works, Volume I', 'Oliver Wendell Holmes: "Old Ironsides", "The Chambered Nautilus", "The Deacon\'s Masterpiece".', '1830–1848', None),
    ('dunbar-poems', 18338, 'The Complete Poems', 'Paul Laurence Dunbar\'s lyrics in standard English and in dialect: "We Wear the Mask", "Sympathy".', '1893–1905', None),
    ('crane-black-riders', 40786, 'The Black Riders and Other Lines', 'Stephen Crane\'s stark free-verse parables of 1895.', '1895', 'free verse'),
    ('crane-war-is-kind', 9870, 'War Is Kind', 'Stephen Crane\'s second book of lines, with the title poem\'s bitter refrain.', '1899', 'free verse'),
    ('melville-battle-pieces', 12384, 'Battle-Pieces and Aspects of the War', 'Melville\'s Civil War poems, from Shiloh to the Confederate surrender.', '1866', None),
    ('lindsay-congo', 1021, 'The Congo and Other Poems', 'Vachel Lindsay\'s chanted "higher vaudeville": "The Congo", "Abraham Lincoln Walks at Midnight".', '1914', None),
    ('stevens-harmonium', 78743, 'Harmonium', 'Wallace Stevens\'s first book: "Sunday Morning", "The Emperor of Ice-Cream", "Thirteen Ways of Looking at a Blackbird".', '1923', None),
    ('williams-al-que-quiere', 51997, 'Al Que Quiere!', 'William Carlos Williams\'s early free verse: "Danse Russe", "Tract", "January Morning".', '1917', 'free verse'),
    ('williams-sour-grapes', 35667, 'Sour Grapes', 'Williams in 1921: "The Great Figure", "Queen-Anne\'s-Lace", "The Widow\'s Lament in Springtime".', '1921', 'free verse'),
    ('pound-personae', 41162, 'Personae', 'Ezra Pound\'s early poems of 1909: masks, troubadours, "Cino", "Na Audiart".', '1909', None),
    ('pound-cathay', 50155, 'Cathay', 'Pound\'s versions of Chinese poems from Fenollosa\'s notes: "The River-Merchant\'s Wife".', '1915', 'free verse'),
    ('pound-lustra', 55564, 'Lustra', 'Pound\'s Imagist and satirical poems: "In a Station of the Metro", "The Garden", "Salutation".', '1916', 'free verse'),
    ('mckay-harlem-shadows', 64989, 'Harlem Shadows', 'Claude McKay\'s sonnets and lyrics of the Harlem Renaissance: "If We Must Die", "The Tropics in New York".', '1922', None),
    ('cullen-color', 70543, 'Color', 'Countee Cullen\'s first book: "Yet Do I Marvel", "Incident", "Heritage".', '1925', None),
    ('hughes-weary-blues', 74745, 'The Weary Blues', 'Langston Hughes\'s first book: the title poem, "The Negro Speaks of Rivers", "Dream Variations".', '1926', None),
    ('toomer-cane', 60093, 'Cane', 'The poems of Jean Toomer\'s Cane: "Reapers", "Georgia Dusk", "Song of the Son".', '1923', None),
    ('clough-amours', 1393, 'Amours de Voyage', 'Clough\'s verse novel in hexameters, told in letters from Rome in 1849.', '1858', None),
    ('dowson-poems', 8497, 'The Poems of Ernest Dowson', 'Dowson\'s Verses and Decorations: "Non sum qualis eram", "Vitae summa brevis".', '1896–1899', None),
    ('thompson-poems', 1469, 'Poems (1893)', 'Francis Thompson\'s first book, with "The Hound of Heaven".', '1893', None),
    ('bridges-shorter-poems', 37804, 'Poetical Works', 'Robert Bridges\'s Shorter Poems and other verse: "London Snow", "Nightingales".', '1873–1912', None),
    ('lazarus-poems', 3295, 'Poems, Volume I', 'Emma Lazarus: "The New Colossus", "In the Jewish Synagogue at Newport".', '1867–1887', None),
    ('riley-farm-rhymes', 4783, 'Riley Farm-Rhymes', 'James Whitcomb Riley\'s Hoosier dialect verse: "When the Frost Is on the Punkin".', '1883–1901', None),
    ('milton-minor-poems', 397, "L'Allegro, Il Penseroso, Comus, and Lycidas", 'Milton\'s early poems: the twin studies of mirth and melancholy, the masque, and the pastoral elegy for Edward King.', '1631–1645', None),
    ('blake-poems', 574, 'Poems of William Blake', 'Blake beyond the Songs: Poetical Sketches, the Book of Thel, and the lyrics of the Rossetti manuscript.', '1783–1794', None),
    ('langland-piers-plowman', 43660, 'The Vision of Piers Plowman', 'Langland\'s fourteenth-century alliterative dream vision in Wright\'s Middle English text, Volume 1.', '1370–1390', 'alliterative verse'),
    ('barnes-dorset', 21785, 'Poems of Rural Life in the Dorset Dialect', 'William Barnes\'s Dorset poems, which Hardy edited and revered.', '1844–1862', None),
    ('gilbert-bab-ballads', 931, 'The Bab Ballads', 'W. S. Gilbert\'s comic ballads, the seed of the Savoy operas.', '1869', None),
    ('graves-fairies', 10122, 'Fairies and Fusiliers', 'Robert Graves\'s war poems of 1917.', '1917', None),
    ('mew-farmers-bride', 71305, "The Farmer's Bride", 'Charlotte Mew\'s one book: the title poem, "The Changeling", "Madeleine in Church".', '1916', None),
    ('rosenberg-poems', 66889, 'Poems', 'Isaac Rosenberg\'s trench poems, published after his death in 1918: "Break of Day in the Trenches".', '1922', None),
    ('gurney-severn-somme', 63895, 'Severn and Somme', 'Ivor Gurney\'s first book, written in the trenches in 1917.', '1917', None),
    ('crane-hart-white-buildings', 77837, 'White Buildings', 'Hart Crane\'s first book: "Voyages", "At Melville\'s Tomb", "Chaplinesque".', '1926', None),
    ('moore-poems', 62833, 'Poems', 'Marianne Moore\'s first book, printed in London without her knowledge: "Poetry", "The Fish".', '1921', 'free verse'),
    ('frost-mountain-interval', 29345, 'Mountain Interval', 'Frost\'s third book: "The Road Not Taken", "Birches", "Out, Out—".', '1916', None),
    ('frost-new-hampshire', 58611, 'New Hampshire', 'Frost\'s Pulitzer book: "Stopping by Woods on a Snowy Evening", "Fire and Ice", "Nothing Gold Can Stay".', '1923', None),
    ('drayton-minor-poems', 17873, 'Minor Poems', 'Michael Drayton: the Idea sonnets, "Since there\'s no help", the Ballad of Agincourt.', '1594–1619', None),
    ('daniel-delia', 18842, 'Delia, with Constable\'s Diana', 'Samuel Daniel\'s sonnet sequence of 1592, printed with Henry Constable\'s Diana.', '1592', 'sonnet'),
    ('thoreau-poems', 59988, 'Poems of Nature', 'Thoreau\'s verse, selected by Sanborn and Salt.', '1895', None),
    ('shelley-prometheus', 'shelley, percy | prometheus unbound', 'Prometheus Unbound, with Other Poems', 'Shelley\'s lyrical drama of the Titan\'s release, printed in 1820 with the odes and lyrics of his greatest year, including "Ode to the West Wind" and "To a Skylark".', '1820', None),
    ('lyrical-ballads', 'lyrical ballads with a few other poems', 'Lyrical Ballads', 'The 1798 volume by Wordsworth and Coleridge that opened English Romanticism, with "Tintern Abbey" and the first Ancient Mariner.', '1798', None),
    ('blake-songs', 'blake songs of innocence and of experience', 'Songs of Innocence and of Experience', 'Blake\'s paired visions of the two contrary states of the human soul: "The Lamb", "The Tyger", "London".', '1789–1794', None),
    ('burns-poems', 'poems and songs of robert burns', 'Poems and Songs', 'The Scots poet\'s songs and satires: "To a Mouse", "Tam o\' Shanter", "Auld Lang Syne".', '1786–1796', None),
    ('milton-paradise-lost', 'milton paradise lost', 'Paradise Lost', 'Milton\'s epic in blank verse on the fall of the angels and of man.', '1667', 'blank verse'),
    ('pope-rape-of-the-lock', 'pope rape of the lock', 'The Rape of the Lock', 'Pope\'s mock epic in heroic couplets over a stolen curl of hair.', '1712', 'heroic couplets'),
    ('tennyson-idylls', 'tennyson idylls of the king', 'Idylls of the King', 'Tennyson\'s Arthurian cycle in blank verse.', '1859–1885', 'blank verse'),
    ('tennyson-poems', 'tennyson, alfred | poems', 'Poems', 'Tennyson\'s early volumes: "The Lady of Shalott", "Ulysses", "The Lotos-Eaters".', '1832–1842', None),
    ('browning-dramatic-lyrics', 'browning, robert | dramatic romances', 'Dramatic Lyrics', 'Robert Browning\'s first collection of monologues, including "My Last Duchess" and "The Pied Piper".', '1842', None),
    ('browning-men-and-women', 'browning men and women', 'Men and Women', 'Browning\'s central book of dramatic monologues.', '1855', None),
    ('barrett-browning-sonnets', 'sonnets from the portuguese', 'Sonnets from the Portuguese', 'Elizabeth Barrett Browning\'s forty-four love sonnets, in the Petrarchan form: an octave rhyming ABBAABBA and a sestet CDCDCD.', '1850', 'petrarchan'),
    ('dickinson-poems', 'poems by emily dickinson three series complete', 'Poems', 'The three series of Dickinson\'s poems as first published in the 1890s.', '1890–1896', None),
    ('whitman-leaves', 'whitman leaves of grass', 'Leaves of Grass', 'Whitman\'s lifelong book of free verse.', '1855–1892', 'free verse'),
    ('poe-poems', 'poe, edgar | poetical works', 'The Complete Poetical Works', 'Poe\'s poems: "Annabel Lee", "The Bells", "Ulalume".', '1827–1849', None),
    ('longfellow-hiawatha', 'longfellow song of hiawatha', 'The Song of Hiawatha', 'Longfellow\'s epic in trochaic tetrameter.', '1855', 'trochaic tetrameter'),
    ('longfellow-evangeline', 'longfellow evangeline', 'Evangeline', 'A tale of Acadie in English hexameters.', '1847', 'dactylic hexameter'),
    ('whittier-snow-bound', 'whittier snow-bound', 'Snow-Bound', 'Whittier\'s winter idyl of a New England farmhouse.', '1866', None),
    ('rossetti-goblin-market', 'rossetti goblin market', 'Goblin Market and Other Poems', 'Christina Rossetti\'s first book.', '1862', None),
    ('dg-rossetti-poems', 'rossetti, dante | poems', 'Poems', 'Dante Gabriel Rossetti\'s sonnets and ballads, including "The Blessed Damozel".', '1870', None),
    ('hopkins-poems', 'hopkins, gerard | poems', 'Poems', 'Hopkins\'s sprung-rhythm poems, published posthumously by Robert Bridges.', '1918', None),
    ('housman-shropshire-lad', 'housman a shropshire lad', 'A Shropshire Lad', 'Sixty-three short lyrics of loss and the English countryside.', '1896', None),
    ('hardy-wessex-poems', 'hardy wessex poems', 'Wessex Poems and Other Verses', 'Hardy\'s first book of verse.', '1898', None),
    ('kipling-barrack-room', 'kipling barrack-room ballads', 'Barrack-Room Ballads', 'Kipling\'s soldiers\' songs, with "Danny Deever" and "Gunga Din".', '1892', None),
    ('yeats-wind-among-reeds', 'yeats wind among the reeds', 'The Wind Among the Reeds', 'Yeats\'s early symbolist lyrics.', '1899', None),
    ('yeats-responsibilities', 'yeats responsibilities', 'Responsibilities', 'Yeats turning toward his harder middle style.', '1914', None),
    ('frost-north-of-boston', 'frost north of boston', 'North of Boston', 'Frost\'s blank-verse narratives of New England: "Mending Wall", "The Death of the Hired Man".', '1914', None),
    ('frost-boys-will', 'frost a boy\'s will', 'A Boy\'s Will', 'Frost\'s first book of lyrics.', '1913', None),
    ('eliot-prufrock', 'eliot prufrock and other observations', 'Prufrock and Other Observations', 'Eliot\'s first collection.', '1917', None),
    ('owen-poems', 'owen, wilfred | poems', 'Poems', 'Wilfred Owen\'s war poems, edited by Siegfried Sassoon.', '1920', None),
    ('sassoon-counter-attack', 'sassoon counter-attack', 'Counter-Attack and Other Poems', 'Sassoon\'s trench poems.', '1918', None),
    ('brooke-1914', 'brooke 1914 and other poems', '1914 and Other Poems', 'Rupert Brooke\'s war sonnets and earlier lyrics.', '1915', None),
    ('spenser-amoretti', 'spenser, edmund | amoretti', 'Amoretti and Epithalamion', 'Spenser\'s sonnet sequence and marriage hymn.', '1595', None),
    ('sidney-astrophel', 'sidney astrophel and stella', 'Astrophel and Stella', 'Sidney\'s sonnet sequence, the first great one in English.', '1591', None),
    ('donne-poems', 'donne poems of john donne', 'Poems', 'Donne\'s songs, sonnets, elegies and holy sonnets.', '1633', None),
    ('herbert-temple', 'herbert, george | temple', 'The Temple', 'George Herbert\'s sacred poems.', '1633', None),
    ('marvell-poems', 'marvell, andrew | poems', 'Poems', 'Andrew Marvell: "To His Coy Mistress", "The Garden".', '1681', None),
    ('herrick-hesperides', 'herrick hesperides', 'Hesperides', 'Herrick\'s lyrics: "To the Virgins", "Delight in Disorder".', '1648', None),
    ('gray-poems', 'gray, thomas | poems', 'Poems', 'Thomas Gray, including the "Elegy Written in a Country Churchyard".', '1751', None),
    ('cowper-task', 'cowper the task', 'The Task', 'Cowper\'s blank-verse poem of the domestic and the natural.', '1785', 'blank verse'),
    ('byron-childe-harold', 'byron childe harold', 'Childe Harold\'s Pilgrimage', 'Byron\'s travel poem in Spenserian stanzas that made him famous overnight.', '1812–1818', 'spenserian'),
    ('scott-lady-of-the-lake', 'scott lady of the lake', 'The Lady of the Lake', 'Scott\'s Highland romance in tetrameter couplets.', '1810', None),
    ('moore-irish-melodies', 'moore, thomas | irish melodies', 'Irish Melodies', 'Thomas Moore\'s songs set to Irish airs.', '1808–1834', None),
    ('clare-poems', 'clare, john | poems', 'Poems', 'John Clare, the Northamptonshire peasant poet.', '1820–1835', None),
    ('hood-poems', 'hood, thomas | poems', 'Poems', 'Thomas Hood, comic and serious.', '1827–1845', None),
    ('arnold-poems', 'arnold, matthew | poems', 'Poems', 'Matthew Arnold: "Dover Beach", "The Scholar-Gipsy".', '1849–1867', None),
    ('swinburne-poems-ballads', 'swinburne poems and ballads', 'Poems and Ballads', 'Swinburne\'s scandalous first series.', '1866', None),
    ('meredith-modern-love', 'meredith, george | modern love', 'Modern Love', 'Meredith\'s sequence of sixteen-line sonnets on a failing marriage.', '1862', None),
    ('morris-defence-guenevere', 'morris defence of guenevere', 'The Defence of Guenevere', 'William Morris\'s Arthurian and medieval poems.', '1858', None),
    ('wilde-reading-gaol', 'wilde ballad of reading gaol', 'The Ballad of Reading Gaol', 'Wilde\'s prison ballad.', '1898', None),
    ('stevenson-childs-garden', 'stevenson child\'s garden of verses', 'A Child\'s Garden of Verses', 'Stevenson\'s poems for and about childhood.', '1885', None),
    ('lear-nonsense', 'lear book of nonsense', 'A Book of Nonsense', 'Edward Lear\'s limericks.', '1846', 'limerick'),
    ('carroll-snark', 'carroll hunting of the snark', 'The Hunting of the Snark', 'Carroll\'s nonsense epic in eight fits.', '1876', None),
    ('bryant-poems', 'bryant, william cullen | poems', 'Poems', 'William Cullen Bryant: "Thanatopsis", "To a Waterfowl".', '1821–1876', None),
    ('emerson-poems', 'emerson, ralph | poems', 'Poems', 'Emerson\'s verse.', '1847', None),
    ('lanier-poems', 'lanier, sidney | poems', 'Poems', 'Sidney Lanier, the musician poet of the South.', '1884', None),
    ('dunbar-lyrics', 'dunbar, paul | lyrics', 'Lyrics of Lowly Life', 'Paul Laurence Dunbar\'s breakthrough book.', '1896', None),
    ('wheatley-poems', 'wheatley poems on various subjects', 'Poems on Various Subjects, Religious and Moral', 'Phillis Wheatley, the first African American poet to publish a book.', '1773', None),
    ('millay-renascence', 'millay renascence and other poems', 'Renascence and Other Poems', 'Edna St. Vincent Millay\'s first book.', '1917', None),
    ('sandburg-chicago', 'sandburg, carl | chicago poems', 'Chicago Poems', 'Sandburg\'s free-verse city.', '1916', 'free verse'),
    ('masters-spoon-river', 'masters spoon river anthology', 'Spoon River Anthology', 'Epitaphs of a small town, spoken by the dead.', '1915', 'free verse'),
    ('robinson-children-of-night', 'robinson children of the night', 'The Children of the Night', 'Edwin Arlington Robinson\'s Tilbury Town: "Richard Cory".', '1897', None),
    ('teasdale-love-songs', 'teasdale love songs', 'Love Songs', 'Sara Teasdale\'s Pulitzer-winning lyrics.', '1917', None),
    ('joyce-chamber-music', 'joyce chamber music', 'Chamber Music', 'James Joyce\'s early lyrics.', '1907', None),
    ('service-sourdough', 'service songs of a sourdough', 'Songs of a Sourdough', 'Robert Service\'s Yukon ballads: "The Cremation of Sam McGee".', '1907', None),
    ('thomas-edward-poems', 'thomas, edward | poems', 'Poems', 'Edward Thomas, killed at Arras in 1917.', '1917', None),
    ('lowell-amy-sword-blades', 'lowell, amy | sword blades', 'Sword Blades and Poppy Seed', 'Amy Lowell\'s imagist collection.', '1914', None),
    ('hd-sea-garden', 'doolittle | sea garden', 'Sea Garden', 'H.D.\'s first book of imagist poems.', '1916', 'free verse'),
    ('johnson-fifty-years', 'johnson, james weldon | fifty years', 'Fifty Years and Other Poems', 'James Weldon Johnson.', '1917', None),
    ('smith-elegiac-sonnets', 'smith, charlotte | sonnets', 'Elegiac Sonnets', 'Charlotte Smith\'s sonnets, which revived the form in English.', '1784', 'sonnet'),
    # ---- batch of 11 Sep 2026: the medieval and historical gap, and more of the tradition
    ('oxford-ballads', 44593, 'The Oxford Book of Ballads', 'The traditional ballads of England and Scotland: Sir Patrick Spens, The Wife of Usher\'s Well, Edward, Tam Lin, the Border raids and the murder ballads, as Quiller-Couch gathered them.', 'before 1800', 'ballad meter'),
    ('percy-reliques', 45939, 'Reliques of Ancient English Poetry, Volume I', 'The book that began the ballad revival in 1765 and taught the Romantics their measure.', '1765', 'ballad meter'),
    ('child-ballads', 37031, 'English and Scottish Ballads, Volume I', 'Francis James Child\'s first gathering of the popular ballads, with his headnotes.', '1857', 'ballad meter'),
    ('gower-confessio', 266, 'Confessio Amantis', 'The Lover\'s Confession: Gower\'s frame of tales on the seven deadly sins, in octosyllabic couplets, written for Richard II.', '1390', 'iambic tetrameter'),
    ('skelton-poems', 59997, 'Poetical Works, Volume I', 'John Skelton, tutor to Henry VIII and the roughest voice of the early Tudor court: the tumbling short lines called Skeltonics.', '1500–1529', None),
    ('davies-poems', 44977, 'The Complete Poems, Volume I', 'Sir John Davies: Orchestra, a poem of dancing, and Nosce Teipsum on the soul.', '1596–1599', None),
    ('breton-poems', 22001, 'Pastoral Poems and Selected Poetry', 'Nicholas Breton, the Elizabethan pastoralist.', '1597–1604', None),
    ('corbet-poems', 65375, 'Poems', 'Richard Corbet, Bishop of Oxford and of Norwich: the Fairies\' Farewell and the drinking songs of a worldly churchman.', '1647', None),
    ('stanley-lyrics', 32986, 'Original Lyrics', 'Thomas Stanley, translator of the Greek anthologists and a Cavalier lyric poet.', '1651', None),
    ('waller-denham', 12322, 'Poetical Works', 'Edmund Waller and Sir John Denham, who smoothed the couplet into the instrument Dryden and Pope inherited.', '1645–1668', 'heroic couplets'),
    ('rochester-works', 44891, 'The Works of the Earl of Rochester', 'John Wilmot: the wit, the obscenity and the despair of the Restoration court.', '1680', None),
    ('killigrew-poems', 41076, 'Poems (1686)', 'Anne Killigrew, painter and maid of honour, dead at twenty-five; Dryden wrote her ode.', '1686', None),
    ('wigglesworth-doom', 58716, 'The Day of Doom', 'The Puritan bestseller of colonial New England: the Last Judgment in ballad measure, learned by heart by children.', '1662', 'ballad meter'),
    ('cooke-sotweed', 21346, 'The Sot-weed Factor', 'A satire on Maryland by a tobacco merchant, the first American verse satire.', '1708', 'iambic tetrameter'),
    ('swift-poems', 13621, 'Poems, Volume II', 'Jonathan Swift in verse: the city shower, the lady\'s dressing room, and his own mock elegy.', '1710–1745', 'iambic tetrameter'),
    ('young-night-thoughts', 18827, 'The Poetical Works, Volume II', 'Edward Young\'s Night Thoughts, the graveyard poem that swept Europe.', '1742–1745', 'iambic pentameter'),
    ('akenside-poems', 9814, 'The Poetical Works of Mark Akenside', 'The Pleasures of Imagination, the eighteenth century\'s philosophical blank verse.', '1744', 'blank verse'),
    ('churchill-poems', 8592, 'Poetical Works', 'Charles Churchill, the satirist Byron admired: the Rosciad and the Prophecy of Famine.', '1761–1764', 'heroic couplets'),
    ('beattie-minstrel', 8695, 'The Minstrel and Other Poems', 'James Beattie\'s Minstrel, in Spenserian stanzas, on the growth of a poet\'s mind before Wordsworth.', '1771–1774', None),
    ('macpherson-ossian', 8161, 'Fragments of Ancient Poetry', 'The Ossian fragments: the forgery that gave Europe its idea of the Celtic sublime.', '1760', 'free verse'),
    ('bloomfield-tales', 9093, 'Rural Tales, Ballads and Songs', 'Robert Bloomfield, the shoemaker poet of Suffolk, after the huge success of The Farmer\'s Boy.', '1802', None),
    ('rogers-poems', 13586, 'Poems', 'Samuel Rogers, the banker poet of The Pleasures of Memory, whose breakfasts fed literary London.', '1792–1834', None),
    ('seward-sonnets', 27663, 'Original Sonnets on Various Subjects', 'Anna Seward, the Swan of Lichfield, who kept the sonnet alive between Milton and Wordsworth.', '1799', 'sonnet'),
    ('baillie-poems', 14617, 'Poems (1790)', 'Joanna Baillie\'s first book, the country poems Wordsworth read before Lyrical Ballads.', '1790', None),
    ('bowles-sonnets', 18915, 'The Poetical Works, Volume I', 'William Lisle Bowles, whose sonnets Coleridge said made him a poet.', '1789–1837', 'sonnet'),
    ('williams-helen-poems', 11054, 'Poems (1786)', 'Helen Maria Williams, the radical poet of the French Revolution.', '1786', None),
    ('kirke-white-poems', 7149, 'The Poetical Works of Henry Kirke White', 'The butcher\'s son who died at twenty-one and whom Southey made famous.', '1803–1806', None),
    ('praed-poems', 71008, 'Poems', 'Winthrop Mackworth Praed, the wittiest writer of vers de société in English.', '1820–1839', None),
    ('halleck-fanny', 34762, 'Fanny, with Other Poems', 'Fitz-Greene Halleck, the Knickerbocker satirist of New York.', '1819–1827', None),
    ('drake-culprit-fay', 317, 'The Culprit Fay and Other Poems', 'Joseph Rodman Drake\'s fairy poem of the Hudson, and The American Flag.', '1819', 'iambic tetrameter'),
    ('sigourney-poems', 20504, 'The Man of Uz and Other Poems', 'Lydia Sigourney, the Sweet Singer of Hartford, the most published American poet of her day.', '1862', None),
    ('aytoun-lays', 10945, 'Lays of the Scottish Cavaliers', 'W. E. Aytoun\'s Jacobite ballads, recited in Scottish schoolrooms for a century.', '1849', 'ballad meter'),
    ('thackeray-ballads', 2732, 'Ballads', 'Thackeray in verse: the Ballad of Bouillabaisse, the Chronicle of the Drum, and the comic pieces.', '1849–1855', None),
    ('timrod-poems', 845, 'Poems', 'Henry Timrod, the laureate of the Confederacy, and the elegies after the war.', '1860–1867', None),
    ('harper-poems', 679, 'Poems', 'Frances Ellen Watkins Harper, abolitionist, suffragist, and the most widely read Black poet before Dunbar.', '1854–1871', 'ballad meter'),
    ('stedman-poems', 70763, 'The Poetical Works of Edmund Clarence Stedman', 'Stedman, the critic and banker who arbitrated American verse for thirty years.', '1860–1897', None),
    ('aldrich-poems', 595, "The Sisters' Tragedy, with Other Poems", 'Thomas Bailey Aldrich, editor of the Atlantic and a jeweller of the short lyric.', '1891', None),
    ('markham-lincoln', 54527, 'Lincoln and Other Poems', 'Edwin Markham, whose Man with the Hoe was the most discussed poem in America in 1899.', '1901', None),
    ('cawein-poems', 7796, 'Poems', 'Madison Cawein, the Keats of Kentucky, who wrote the Ohio valley into English verse.', '1911', None),
    ('carman-later-poems', 33417, 'Later Poems', 'Bliss Carman, the Canadian vagabond lyricist.', '1921', None),
    ('lampman-lyrics', 12664, 'Lyrics of Earth', 'Archibald Lampman, the finest of the Canadian Confederation poets.', '1895', None),
    ('roberts-new-poems', 59897, 'New Poems', 'Charles G. D. Roberts, the father of Canadian poetry.', '1919', None),
    ('crawford-poems', 6815, "Old Spookses' Pass, Malcolm's Katie and Other Poems", 'Isabella Valancy Crawford, who died unknown in a Toronto lodging and is now read as Canada\'s first great poet.', '1884', None),
    ('guiney-songs', 53087, 'Songs at the Start', 'Louise Imogen Guiney, the American Catholic poet and scholar of the seventeenth century.', '1884', None),
    ('watson-poems', 13179, 'The Poems of William Watson', 'William Watson, twice passed over for the laureateship, the last of the grand Victorian manner.', '1892–1905', None),
    ('newbolt-poems', 24405, 'Poems: New and Old', 'Henry Newbolt: Drake\'s Drum, Vitaï Lampada, and the sea songs of the Edwardian empire.', '1912', None),
    ('russell-divine-vision', 36913, 'The Divine Vision and Other Poems', 'George William Russell, "AE", the mystic of the Irish revival and Yeats\'s friend and rival.', '1904', None),
    ('field-poems', 36150, 'Hoosier Lyrics', 'Eugene Field, the children\'s poet of Wynken, Blynken and Nod, in his newspaper voice.', '1905', None),
    ('hull-gael', 46917, 'The Poem-Book of the Gael', 'Irish poetry from the eighth century onward, in Eleanor Hull\'s translations.', '1912', None),
    ('symonds-wine-women', 18044, 'Wine, Women and Song', 'The Latin student songs of the Middle Ages, the Carmina Burana world, in John Addington Symonds\'s versions.', '1884', None),
    ('evans-welsh', 32767, 'Specimens of the Poetry of the Ancient Welsh Bards', 'Evan Evans\'s translations of the Welsh bards, which fed Gray\'s Bard and the Celtic revival.', '1764', None),
    ('bell-ancient-poems', 649, 'Ancient Poems, Ballads and Songs of the Peasantry of England', 'The songs working people actually sang, gathered by Robert Bell.', '1857', 'ballad meter'),
    ('crashaw-poems', 38549, 'Steps to the Temple and Other Poems', 'Richard Crashaw, the English Baroque: sacred poems of ecstasy and tears, and the secular verse beside them.', '1646–1652', None),
    ('chatterton-rowley', 13037, 'The Rowley Poems', 'Chatterton\'s forged medieval poet Thomas Rowley: the poems that fooled the antiquaries and moved the Romantics.', '1777', None),
    ('southey-thalaba', 39804, 'Thalaba the Destroyer', 'Southey\'s Arabian romance in irregular unrhymed verse, an epic of a young destroyer of sorcerers.', '1801', None),
    ('landor-poems', 21628, 'Imaginary Conversations and Poems', 'Landor\'s lapidary lyrics and epigrams, with a selection of the prose dialogues.', '1795–1863', None),
    ('moore-lalla-rookh', 76794, 'Lalla Rookh', 'Thomas Moore\'s oriental romance: four tales in verse told to a princess on her journey to Cashmere.', '1817', None),
    ('patmore-angel', 4099, 'The Angel in the House', 'Patmore\'s Victorian poem of courtship and marriage, in quatrains.', '1854–1862', None),
    ('henley-poems', 1568, 'Poems', 'W. E. Henley: "Invictus", the hospital poems, London Voluntaries.', '1898', None),
    ('johnson-lionel-poems', 66520, 'Poems', 'Lionel Johnson of the Rhymers\' Club: "By the Statue of King Charles at Charing Cross", "The Dark Angel".', '1895', None),
    ('de-la-mare-peacock-pie', 3753, 'Peacock Pie', 'Walter de la Mare\'s book of rhymes for children and everyone else.', '1913', None),
    ('chesterton-white-horse', 1719, 'The Ballad of the White Horse', 'Chesterton\'s ballad epic of Alfred and the Danes.', '1911', None),
    ('masefield-salt-water', 52761, 'Salt-Water Ballads', 'Masefield\'s first book: "Sea-Fever" and the sailors\' ballads.', '1902', None),
    ('freneau-poems', 38475, 'Poems', 'Philip Freneau, poet of the American Revolution: "The Wild Honey Suckle", "The Indian Burying Ground".', '1786–1815', None),
    ('wylie-nets', 6682, 'Nets to Catch the Wind', 'Elinor Wylie\'s first book, cool and exact: "Velvet Shoes", "Wild Peaches".', '1921', None),
    ('ingelow-poems', 13223, 'Poems, Volume I', 'Jean Ingelow: "Divided", "The High Tide on the Coast of Lincolnshire".', '1863', None),
    ('meynell-poems', 1186, 'Poems', 'Alice Meynell\'s spare, exact lyrics: "Renouncement", "The Shepherdess".', '1893', None),
    ('kilmer-trees', 263, 'Trees and Other Poems', 'Joyce Kilmer: "Trees" and the poems of a life cut short in France.', '1914', None),
    ('seeger-poems', 617, 'Poems', 'Alan Seeger: "I Have a Rendezvous with Death" and the poems of the Foreign Legion.', '1916', None),
    ('lovelace-lucasta', 703, 'Lucasta', 'Richard Lovelace, Cavalier: "To Lucasta, Going to the Wars", "To Althea, from Prison".', '1649', None),
    ('meredith-poems', 1381, 'Poems, Volume I', 'George Meredith: Modern Love, the sonnet sequence of a marriage failing, and the early poems.', '1851–1862', None),
    ('bronte-poems', 1019, 'Poems by Currer, Ellis, and Acton Bell', 'The Brontë sisters\' one joint book: Emily\'s "Remembrance" and "No Coward Soul Is Mine" among them.', '1846', None),
    ('traherne-poems', 61586, 'Poetical Works', 'Thomas Traherne, found in manuscript two centuries late: the poems of felicity and childhood.', '1903', None),
    ('collins-poems', 29879, 'Poetical Works', 'William Collins: the Odes of 1746, "Ode to Evening", "How Sleep the Brave".', '1746', None),
    ('benet-young-adventure', 312, 'Young Adventure', 'Stephen Vincent Benét\'s first book of poems, written at twenty.', '1918', None),
    ('hemans-poems', 'hemans | poems', 'Poems', 'Felicia Hemans: "Casabianca".', '1808–1835', None),
    ('bradstreet-tenth-muse', 'bradstreet, anne | muse', 'The Tenth Muse', 'Anne Bradstreet, the first published poet of the American colonies.', '1650', None),
    ('marlowe-hero-leander', 'marlowe hero and leander', 'Hero and Leander', 'Marlowe\'s erotic epyllion in heroic couplets.', '1598', 'heroic couplets'),
    ('shakespeare-venus-adonis', 'shakespeare venus and adonis', 'Venus and Adonis', 'Shakespeare\'s narrative poem in six-line stanzas.', '1593', None),
    ('dryden-absalom', 'dryden, john | absalom', 'Absalom and Achitophel', 'Dryden\'s political satire in heroic couplets.', '1681', 'heroic couplets'),
    ('thomson-seasons', 'thomson, james, 1700 | seasons', 'The Seasons', 'James Thomson\'s blank-verse year.', '1730', 'blank verse'),
    ('crabbe-village', 'crabbe the village', 'The Village', 'George Crabbe\'s unsentimental rural poem in couplets.', '1783', 'heroic couplets'),
    ('lawrence-amores', 'lawrence amores', 'Amores', 'D. H. Lawrence\'s early poems.', '1916', None),
    ('holmes-poems', 'holmes, oliver wendell | poems', 'Poems', 'Oliver Wendell Holmes: "Old Ironsides", "The Chambered Nautilus".', '1836–1890', None),
    ('lowell-james-russell-poems', 'lowell, james russell | poems', 'Poems', 'James Russell Lowell.', '1844–1888', None),
    ('landon-poems', 'landon, letitia | poe', 'Poems', 'Letitia Elizabeth Landon (L.E.L.).', '1824–1838', None),
    # The verse dramas. Each was printed inside a collection, and the parser read every speech as a
    # poem of its own: Longfellow's Christus was some 250 "poems" named after whoever was speaking,
    # and Poe's Politian was inside "The City in the Sea". They are published here as the plays they
    # are, a section to a scene, and taken out of the collection they came from (see SLUG_META).
    ('longfellow-christus', 1365, 'Christus: A Mystery', "Longfellow's trilogy on the Christian ages: the Divine Tragedy, the Golden Legend, the New England Tragedies.", '1872', None),
    ('longfellow-judas-maccabaeus', 1365, 'Judas Maccabaeus', "Longfellow's tragedy in five acts on the Maccabean revolt.", '1872', None),
    ('longfellow-michael-angelo', 1365, 'Michael Angelo: A Fragment', "Longfellow's unfinished dramatic poem on the sculptor's last years, published after his death.", '1883', None),
    ('lazarus-spagnoletto', 3295, 'The Spagnoletto', "Emma Lazarus's tragedy in five acts, on the painter Ribera and his daughter.", '1876', None),
    ('poe-politian', 79019, 'Politian', "Poe's only play: five scenes of an unfinished tragedy set in Rome.", '1835', None),
]

# Epics with explicit Gutenberg editions. Non-English originals use public domain English verse translations.
# (slug, gutenberg id, title, original author, author dates, lang, composed year, translator, translation year, blurb, meter hint, scheme)
# per-work parsing hints for the generic parser (see generic.parse_gutenberg)
SLUG_META = {
    # --- the verse dramas, and the collections they are taken out of -------------------------
    'longfellow-christus': {'start_at': r'^CHRISTUS: A MYSTERY$', 'stop_at': r'^JUDAS MACCABAEUS\.$',
                            'drama': True, 'book_prefix': True, 'titlere': r"^[A-Z][A-Z' ,\-]{3,46}$"},
    'longfellow-judas-maccabaeus': {'start_at': r'^JUDAS MACCABAEUS\.$', 'stop_at': r'^MICHAEL ANGELO$',
                                    'stop_occurrence': 2, 'drama': True, 'book_prefix': True,
                                    'titlere': r'^(ACT|SCENE)\b'},
    'longfellow-michael-angelo': {'start_at': r'^MICHAEL ANGELO$', 'start_occurrence': 2,
                                  'stop_at': r'^TRANSLATIONS$', 'drama': True, 'book_prefix': True,
                                  'titlere': r"^(PART |PROLOGUE|MONOLOGUE|[A-Z][A-Z' ,\-]{3,46})$"},
    'lazarus-spagnoletto': {'start_at': r'^THE SPAGNOLETTO\.$', 'drama': True, 'book_prefix': True,
                            'titlere': r'^(ACT\.? |SCENE )'},
    'poe-politian': {'start_at': r'^SCENES FROM .POLITIAN;.$', 'stop_at': r'^AL AARAAF\.\[2\]$',
                     'drama': True, 'book_prefix': True, 'flush_titles': True,
                     'titlere': r'^(ROME\.|_?[A-Z][a-z])'},
    # Christus, Judas Maccabaeus and Michael Angelo run one after another in the middle of the
    # Longfellow file, with the translations after them; Politian sits between two poems.
    'longfellow-poems': {'drop_range': [(r'^CHRISTUS: A MYSTERY$', r'^TRANSLATIONS$')]},
    'poe-poems': {'drop_range': [(r'^SCENES FROM .POLITIAN;.$', r'^AL AARAAF\.\[2\]$')]},
    'lazarus-poems': {'stop_at': r'^THE SPAGNOLETTO\.$'},
    'masters-spoon-river': {'start_at': r'^The Hill$', 'start_occurrence': 1, 'start_inclusive': True},
    'hopkins-poems': {'number_parts': True},
    'goldsmith-poems': {'start_at': r'^THE TRAVELLER$', 'start_occurrence': 2, 'start_inclusive': True, 'stop_at': r'^INTRODUCTION$', 'stop_occurrence': 2, 'skipre': r'^(DEDICATION|TO SIR JOSHUA REYNOLDS|PORTRAIT OF GOLDSMITH|AFTER REYNOLDS|GOLDSMITH.S AUTOGRAPH|DESCRIPTIVE POEMS|LYRICAL AND MISCELLANEOUS)$',
                        'titlemap': {'A PROSPECT OF SOCIETY': 'The Traveller', 'THE DEPARTURE': 'The Deserted Village', 'PRESERVED BY MACROBIUS': 'Prologue of Laberius', 'IN IMITATION OF DEAN SWIFT': 'The Logicians Refuted', 'A POEM': 'Retaliation', 'POSTSCRIPT': 'Retaliation', 'A POETICAL EPISTLE TO LORD CLARE': 'The Haunch of Venison', 'SONG': 'Song Intended for ‘She Stoops to Conquer’', 'THE ROSCIAD, A POEM, BY THE AUTHOR': 'An Epigram Addressed to the Gentlemen Reflected on in The Rosciad', 'ROSCOM': 'An Epigram Addressed to the Gentlemen Reflected on in The Rosciad', 'ON SEEING MRS. PERFORM IN THE CHARACTER OF': 'On Seeing Mrs. —— Perform in the Character of ——', 'OF THE DEATH OF THE LEFT HON': 'Of the Death of the Left Hon. ——', 'A TALE': 'The Double Transformation: A Tale', 'IN THE MANNER OF SWIFT': 'A New Simile, in the Manner of Swift', 'A BALLAD': 'Edwin and Angelina: A Ballad', 'THE CAPTIVITY': 'The Captivity: An Oratorio', 'THE CAPTIVITY AN ORATORIO': 'The Captivity: An Oratorio', 'THE CAPTIVITY AN': 'The Captivity: An Oratorio', 'THE CAPTIVITY ACT I—SCENE I': 'The Captivity: An Oratorio', 'VIDA’S GAME OF CHESS': 'Vida’s Game of Chess', 'EPILOGUE': 'Epilogue Intended for ‘She Stoops to Conquer’', 'TRANSLATION': 'Translation: “Chaste Are Their Instincts”'},
                        'fold_into_prev': r'^(Air|Recitative|Chorus|Semi-Chorus|Miss Catley|Mrs\.? |Mr\.? |First|Second|Third|The Last Chorus|Chaldean|Israelitish|Prophet|Priest|Song)\b',
                        'ignore_heading': r'^(INTENDED TO HAVE BEEN (SPOKEN|SUNG) (FOR|IN)|‘SHE STOOPS TO CONQUER’|AN|ORATORIO|TRANSLATED|SCENE [IVX]+|ACT [IVX]+)\.?$', 'drop_block': r'^THE CAPTIVITY$', 'carry_title': r'^The Captivity'},
    'canterbury-tales-orig': {'start_at': r'(?i)^HERE BIGINNETH THE BOOK OF THE TALES', 'start_inclusive': True},
    'browning-dramatic-lyrics': {'flush_titles': True, 'note_block': r'^NOTES:?$',
                                 # this edition prints the poem's title in capitals at the margin and its subtitle
                                 # indented under it, so the subtitle is what the parser sees; and it breaks The
                                 # Heretic's Tragedy into its own stage labels. Put both back.
                                 'fold_into_prev': r'^(Poem|Chorus) [IVXL]+$|^Subjoineth the Abbot',
                                 # Holy-Cross Day is numbered from II, which makes the fold swallow the poem
                                 # printed after it; cut Protus back out at its first line.
                                 'split_lines': [(r'^Among these latter busts we count by scores', 'Protus')],
                                 'titlemap': {'anoldstory': 'The Patriot', 'ferrara': 'My Last Duchess',
                                              'aixenprovence': 'Count Gismond',
                                              'shortlyafterthe revivaloflearningineurope': "A Grammarian's Funeral",
                                              'shortlyaftertherevivaloflearningineurope': "A Grammarian's Funeral",
                                              'amiddleageinterlude': "The Heretic's Tragedy",
                                              "A GRAMMARIAN'S FUNERAL,": "A Grammarian's Funeral",
                                              'preadmonisheththeabbotdeodaet': "The Heretic's Tragedy"},
                                 'note_block_source': "The editor's note on this poem, from Dramatic Romances (Project Gutenberg #4253)."},
    'beowulf-orig': {'start_at': r'^B[ĒE]OWULF\.$', 'stop_at': r'^THE FIGHT AT FINNSBURH', 'stop_occurrence': 2, 'caesura_gap': True, 'numbered_titles': True, 'partlabel': 'Fitt'},
    'crashaw-poems': {'start_at': r'^STEPS TO THE TEMPLE\.?$', 'stop_at': r'^FOOTNOTES:', 'skipre': r'^SO THE SANCROFT MS.*'},
    'chatterton-rowley': {'start_at': r'^(?i)eclogue the first\.?$', 'start_occurrence': 2, 'start_inclusive': True, 'stop_at': r'^A GLOSSARY OF UNCOMMON WORDS'},
    'southey-thalaba': {'foldsub': True, 'stop_at': r'^FOOTNOTES:', 'carry_title': r'^Book [IVXL]+$', 'min_lines': 1},
    'landor-poems': {'start_at': r'^POEMS\.?$', 'start_occurrence': 2, 'first_line_titles': True, 'no_fold': True},
    'henley-poems': {'first_line_titles': True},
    'moore-lalla-rookh': {'start_at': r'^PREFACE\.$', 'stop_at': r'^(THE END\.|NOTES\.?|AZAB OR SABA\.?)$', 'split_lines': [(r'^One morn a Peri at the gate', 'PARADISE AND THE PERI')]},
    'masefield-salt-water': {'stop_at': r'^GLOSSARY', 'stop_occurrence': 2},
    'freneau-poems': {'start_at': r'^PART I$', 'start_occurrence': 2, 'stop_at': r'^END OF VOL'},
    'seeger-poems': {'start_at': r'^\s*An Ode to Natural Beauty\s*$', 'start_inclusive': True},
    'lovelace-lucasta': {'start_at': r'^LUCASTA:$', 'stop_at': r'^THE END\.$', 'skipre': r'^(THE DEDICATION|VERSES ADDRESSED TO THE AUTHOR|TO MY DEAR FRIEND THE AUTHOR|TO THE RIGHT HON.*|TO MY BEST BROTHER.*|AD EUNDEM|ON THE POEMS|CARMEN EROTICUM|ANOTHER, UPON THE POEMS|.*EXASTIKON.*|UPON MY NOBLE FRIEND.*|BEING IN HOLLAND.*|TO (HIS|MY|COLONEL).*LOVELACE.*|.*PERI TOY AYTOY.*|POEMS|BY RICHARD LOVELACE, ESQ.*)\.?$'},
    'traherne-poems': {'start_at': r'^THE SALUTATION$', 'start_inclusive': True, 'stop_at': r'^(SIDELIGHTS ON CHARLES LAMB|WORKS PREPARING|FOOTNOTES:)'},
    'collins-poems': {'start_at': r'^ORIENTAL ECLOGUES\.$', 'start_occurrence': 2, 'stop_at': r'^THE END\.$', 'skipre': r'^(PREFACE|AND NOW TRANSLATED|ON SEVERAL DESCRIPTIVE.*)\.?$'},
    'benet-young-adventure': {'start_at': r'^I\. The Drug-Shop', 'start_inclusive': True},
    'horace-odes': {'numbered_titles': True, 'partlabel': 'Ode', 'book_prefix': True, 'titlemap': {'PHOEBE, SILVARUMQUE': 'Carmen Saeculare'}, 'stop_at': r'^NOTES\.$', 'start_at': r'^THE ODES OF HORACE\.$'},
    'juvenal-satires': {'start_at': r'^BY WILLIAM GIFFORD, ESQ\.$', 'start_occurrence': 3, 'stop_at': r'^PERSIUS\.$', 'stop_occurrence': 2, 'ignore_heading': r'^(ARGUMENT|THE ARGUMENT)\.?$', 'subtitle_join': True},
    'hesiod-works': {'start_at': r'^THE WORKS AND DAYS\.$', 'stop_at': r'^WITH GLOSSARIAL', 'skipre': r'^(COWPER|DRYDEN|PITT|WARTON|CLERC|BRYANT|CREECH|FOOTNOTES|HYMN TO .*|THEOCRITUS.*|CATULLUS.*|So .*|.*—.*)\.?$', 'resume_only': (r'^FOOTNOTES', r'^THE (THEOGONY|SHIELD OF HERCULES|WORKS AND DAYS)\b'), 'titlemap': {'WORKS': 'The Works and Days: Works', 'DAYS': 'The Works and Days: Days', 'THE DAYS': 'The Works and Days: Days'}},
    'oxford-ballads': {'titlere': r'^\d{1,3}\.\s+\S.*$', 'title_sub': (r'^\d{1,3}\.\s*', ''), 'start_at': r'^BOOK I$', 'start_occurrence': 2},
    'child-ballads': {'start_at': r'^BOOK I\.$', 'start_occurrence': 2, 'stop_at': r'^APPENDIX\.$', 'stop_occurrence': 2},
    'percy-reliques': {'start_at': r'^I\.$', 'start_occurrence': 2, 'stop_at': r'^APPENDIX I\.$', 'stop_occurrence': 2, 'numbered_titles': True, 'partlabel': 'Ballad', 'skipre': r'^(NOTES|GLOSSARY|ERRATA|PREFACE|INTRODUCTION|ADVERTISEMENT|RELIQUES OF)\b'},
    'gower-confessio': {'titlemap': {'INCIPIT LIBER PRIMUS': 'Book I', 'INCIPIT LIBER SECUNDUS': 'Book II', 'INCIPIT LIBER TERCIUS': 'Book III', 'INCIPIT LIBER QUARTUS': 'Book IV', 'INCIPIT LIBER QUINTUS': 'Book V', 'INCIPIT LIBER SEXTUS': 'Book VI', 'INCIPIT LIBER SEPTIMUS': 'Book VII', 'INCIPIT LIBER OCTAUUS': 'Book VIII', 'PROLOGUS': 'Prologue'}},
    'skelton-poems': {'stop_at': r'^NOTES\.?$'},
    'tibullus-elegies': {'start_at': r'^BOOK I$', 'start_occurrence': 2, 'start_inclusive': True, 'subtitle_join': True, 'book_prefix': True, 'titlere': r'^(ELEGY THE \w+|BOOK [IVX]+|[A-Z][A-Z \'’,;.\-]{3,48})$'},
    'dante-vita-nuova': {'numbered_titles': True, 'partlabel': 'Section'},
    'catullus-carmina': {'dual_numbered': True, 'partlabel': 'Carmen', 'numbered_titles': True, 'min_lines': 2, 'start_at': r'^LIBER\.$', 'stop_at': r'^NOTES$'},
    'sidney-astrophel': {'each_stanza': 'Sonnet', 'start_at': r'^\s*Lo[uv]ing in truth', 'start_inclusive': True, 'headre': r'^_?(the )?\w+ sonnet\.?_?$'},
    'eugene-onegin': {'start_at': r'^CANTO THE FIRST', 'start_occurrence': 2},
    'faerie-queene': {'stop_at': r'^NOTES$', 'stop_occurrence': 2},
    'wheatley-poems': {'titlemap': {'O N V I R T U E': 'On Virtue', 'TO M AE C E N A S': 'To Maecenas'}, 'prose_re': r'^Preface$'},
    # Todd and Higginson number every poem and title only some. A numeral alone under a part heading
    # (LIFE, LOVE, NATURE, TIME AND ETERNITY) is an untitled poem, so the part headings are mapped to
    # the book's own title, which makes the numbered poems "Poem N" and lets first_line_titles name
    # them by their first line, as the editors' convention has it. The prefatory poem has no heading
    # at all and is split off at its first line.
    'dickinson-poems': {'first_line_titles': True,
                        # the commonest line length is six syllables in 40% of her lines, which the guess would
                        # publish as 'iambic trimeter'; her measure is the hymn stanza, and it is named by hand
                        'meter': 'common measure', 'form': 'Common measure: quatrains alternating iambic tetrameter and trimeter',
                        'titlemap': {'I. LIFE': 'Poems', 'II. LOVE': 'Poems', 'III. NATURE': 'Poems', 'IV. TIME AND ETERNITY': 'Poems',
                                     'LIFE': 'Poems', 'LOVE': 'Poems', 'NATURE': 'Poems', 'TIME AND ETERNITY': 'Poems'},
                        'split_lines': [(r'^This is my letter to the world', 'This is my letter to the world')]},
    'dowson-poems': {'prose_re': r'^An Orchestral Violin\b'},
    'scott-lady-of-the-lake': {'foldsub': True, 'stop_at': r'^NOTES\.?$'},
    'gray-poems': {'stop_at': r'^NOTES\.$'},
    'hemans-poems': {'stop_at': r'^THE VESPERS OF PALERMO\.$', 'start_at': r'^JUVENILE POEMS\.$', 'start_inclusive': True, 'subtitle_join': True, 'skipre': r'^(JUVENILE POEMS|TRANSLATIONS FROM CAMOENS AND OTHER POETS|MISCELLANEOUS POEMS|TALES AND HISTORIC SCENES|ITALIAN LITERATURE|PATRIOTIC EFFUSIONS OF THE ITALIAN POETS|WELSH MELODIES|SONGS OF THE CID|GREEK SONGS|LAYS OF MANY LANDS|RECORDS OF WOMAN|SONGS OF THE AFFECTIONS|HYMNS FOR CHILDHOOD|NATIONAL LYRICS, AND SONGS FOR MUSIC|NATIONAL LYRICS|SONGS OF A GUARDIAN SPIRIT|SONGS OF SPAIN|SONGS FOR SUMMER HOURS|SONGS OF CAPTIVITY|MISCELLANEOUS LYRICS|SCENES AND HYMNS OF LIFE|SONNETS|FEMALE CHARACTERS OF SCRIPTURE|SONNETS, DEVOTIONAL AND MEMORIAL|SCENES AND PASSAGES FROM GOETHE|THOUGHTS DURING SICKNESS|THE DOMESTIC AFFECTIONS, AND OTHER POEMS)\.?$'},
    'rubaiyat': {'titlemap': {'FIRST EDITION': 'First Edition (1859)', 'FIFTH EDITION': 'Fifth Edition (1889)'}, 'prose_re': r'^Omar Khayyam, the Astronomer'},
    'herrick-hesperides': {'min_lines': 2, 'skipre': r'^LONDON$', 'gloss_lines': "Word-glosses from Pollard's edition (Muses' Library, 1891; Project Gutenberg #22421)."},
    'kalevala': {'append_gids': [33089], 'max_lines': 40000},
    'poetic-edda': {'subtitle_join': True, 'resume_after_note': True, 'start_at': r'^PART I$', 'skipre': r'^(THE POETIC EDDA|VOLUME [IVX]+|LAYS OF THE \w+|PART [IVX]+)$'},
    'nibelungenlied': {'partlabel': 'Adventure', 'numbered_titles': True},
    'pope-rape-of-the-lock': {'start_at': r'^THE RAPE OF THE LOCK$', 'start_occurrence': 3, 'stop_at': r'^APPENDIX$', 'stop_occurrence': 2},
    'canterbury-tales': {'subparts': True, 'stop_at': r'^THE COURT OF LOVE\.$'},
    'wilde-reading-gaol': {'titlemap': {'VERSION TWO': 'The Ballad of Reading Gaol'}, 'skipre': r'^VERSION ONE', 'partlabel': 'Part'},
    'beowulf': {'partlabel': 'Part', 'titlemap': {'PRELUDE OF THE FOUNDER OF THE DANISH HOUSE': 'Prelude'}},
    # found by the September 2026 missing-books scan (Lucan's Book II was the first case)
    'lucan-pharsalia': {'stop_at': r"^PREPARER'S NOTES:$"},                  # the bibliography after Book X was folding into it
    'homer-iliad': {'stop_at': r'^CONCLUDING NOTE\.$', 'stop_occurrence': 2},  # Pope's concluding note and the footnotes were folding into Book XXIV
    'lusiads': {'stop_at': r'^THE END\.$'},                                 # Mickle's footnotes (Latin quotations read as verse) were folding into Book X
    'orlando-furioso': {'max_lines': 45000},                                 # 38,700 lines: the 20,000-line epic cap stopped it inside Canto XXV
    # Wiffen's volume: a prose essay in chapters, then the works. The poems were all folded into 'Chapter V' of the essay.
    # The eclogues are dialogues: cast lists and speaker names are not headings, and the three silvas of Eclogue II are one poem.
    'garcilaso-works': {'start_at': r'^THE WORKS OF GARCILASSO\.$', 'stop_at': r'^APPENDIX\.$', 'no_fold': True,
                        'ignore_heading': r'^(SALICIO|NEMOROSO|ALBANIO|CAMILLA|TYRRENO|ALCINO)([.,] ?(SALICIO|NEMOROSO|ALBANIO|CAMILLA|TYRRENO|ALCINO))*\.?$|^SILVA [IVX]+\.?$|^YES\.?$'},
    'waley-chinese': {'no_foldsub': True, 'start_at': r'^CHAPTER I:?$', 'start_occurrence': 2, 'start_inclusive': True},                                   # 170 poems grouped in chapters: keep the poems, not the chapters
}
EPICS = [
    ('hesiod-works', 66350, 'The Works and Days, the Theogony and the Shield of Hercules', 'Hesiod', (None, None), 'grc', -700, 'Charles Abraham Elton', '1812', 'The farmer\'s calendar, the genealogy of the gods and the shield, in Elton\'s blank verse.', 'blank verse', None),
    ('catullus-carmina', 20732, 'The Carmina', 'Catullus', (-84, -54), 'la', -55, 'Richard Burton', '1894', 'Lesbia, the sparrow, the marriage songs and the invective, in Burton\'s metrical versions.', None, None),
    ('horace-odes', 5432, 'The Odes and Carmen Saeculare', 'Horace', (-65, -8), 'la', -23, 'John Conington', '1863', 'The four books of odes in Conington\'s stanzas, the standard Victorian Horace.', None, None),
    ('juvenal-satires', 50657, 'The Satires', 'Juvenal', (55, 127), 'la', 110, 'William Gifford', '1802', 'Rome\'s angriest poet on the city, women, patrons and the vanity of human wishes, in Gifford\'s couplets.', 'heroic couplets', None),
    ('homer-iliad', 6130, 'The Iliad', 'Homer', (None, None), 'grc', -750, 'Alexander Pope', '1720', 'The wrath of Achilles and the last weeks of the Trojan War, in Pope\'s heroic couplets, the translation Johnson called the noblest version of poetry the world has ever seen.', 'heroic couplets', None),
    ('homer-odyssey', 3160, 'The Odyssey', 'Homer', (None, None), 'grc', -725, 'Alexander Pope', '1726', 'The ten-year homecoming of Odysseus, in the couplets of Pope and his assistants Broome and Fenton.', 'heroic couplets', None),
    ('virgil-aeneid', 228, 'The Aeneid', 'Virgil', (-70, -19), 'la', -19, 'John Dryden', '1697', 'Aeneas from the fall of Troy to the founding of Rome, in Dryden\'s heroic couplets.', 'heroic couplets', None),
    ('ovid-metamorphoses', 28621, 'The Metamorphoses', 'Ovid', (-43, 17), 'la', 8, 'J. J. Howard', '1807', 'Two hundred and fifty tales of transformation from Chaos to Caesar, in English blank verse.', 'blank verse', None),
    ('dante-divine-comedy', 1004, 'The Divine Comedy', 'Dante Alighieri', (1265, 1321), 'it', 1320, 'Henry Wadsworth Longfellow', '1867', 'Hell, Purgatory and Paradise, in Longfellow\'s unrhymed tercets that keep Dante\'s line-by-line sense.', 'blank verse', None),
    ('beowulf', 981, 'Beowulf', 'Anonymous (Old English)', (None, None), 'ang', 900, 'Francis B. Gummere', '1910', 'The oldest English epic: Grendel, Grendel\'s mother and the dragon, in Gummere\'s alliterative four-stress verse.', 'alliterative verse', None),
    ('kalevala', 25953, 'The Kalevala', 'Elias Lönnrot (compiler)', (1802, 1884), 'fi', 1835, 'W. F. Kirby', '1907', 'The Finnish national epic, runos 1 to 25, in the trochaic tetrameter that Longfellow borrowed for Hiawatha.', 'trochaic tetrameter', None),
    ('nibelungenlied', 59831, 'The Lay of the Nibelung Men', 'Anonymous (Middle High German)', (None, None), 'de', 1200, 'Arthur S. Way', '1911', 'Siegfried, Kriemhild, Brunhild and the fall of the Burgundians, in Way\'s long rhymed lines.', None, None),
    ('song-of-roland', 391, 'The Song of Roland', 'Anonymous (Old French)', (None, None), 'fr', 1100, 'C. K. Scott-Moncrieff', '1919', 'Roland at Roncevaux, in a translation that keeps the assonance of the original laisses.', None, None),
    ('orlando-furioso', 615, 'Orlando Furioso', 'Ludovico Ariosto', (1474, 1533), 'it', 1532, 'William Stewart Rose', '1823', 'Ariosto\'s romance epic of Charlemagne\'s paladins, in ottava rima like the original.', None, 'ABABABCC'),
    ('jerusalem-delivered', 392, 'Jerusalem Delivered', 'Torquato Tasso', (1544, 1595), 'it', 1581, 'Edward Fairfax', '1600', 'The First Crusade as Tasso imagined it, in Fairfax\'s Elizabethan ottava rima.', None, 'ABABABCC'),
    ('lusiads', 32528, 'The Lusiad', 'Luís de Camões', (1524, 1580), 'pt', 1572, 'William Julius Mickle', '1776', 'Vasco da Gama\'s voyage to India as Portugal\'s national epic, in Mickle\'s couplets.', 'heroic couplets', None),
    ('lucretius-nature', 785, 'On the Nature of Things', 'Lucretius', (-99, -55), 'la', -55, 'William Ellery Leonard', '1916', 'The Epicurean universe of atoms and void, in Leonard\'s blank verse.', 'blank verse', None),
    ('goethe-faust', 14591, 'Faust, Part One', 'Johann Wolfgang von Goethe', (1749, 1832), 'de', 1808, 'Bayard Taylor', '1870', 'Faust\'s bargain with Mephistopheles, translated in the original metres.', None, None),
    ('eugene-onegin', 23997, 'Eugene Onegin', 'Alexander Pushkin', (1799, 1837), 'ru', 1833, 'Henry Spalding', '1881', 'Pushkin\'s novel in verse, in the fourteen-line Onegin stanza.', None, None),
    # ---- translations added 11 Sep 2026
    ('ovid-amores', 47676, 'The Amores', 'Ovid', (-43, 17), 'la', -16, 'Henry T. Riley', '1885', 'The love elegies: Corinna, the doorkeeper, the rival, the lover as soldier and as slave. The book that taught Europe how to write about love.', None, None),
    ('tibullus-elegies', 9610, 'The Elegies', 'Tibullus', (-55, -19), 'la', -25, 'Theodore Chickering Williams', '1905', 'The gentlest of the Roman elegists: Delia, the countryside, and a wish to die in a lover\'s arms.', None, None),
    ('dante-vita-nuova', 41085, 'The New Life', 'Dante Alighieri', (1265, 1321), 'it', 1294, 'Dante Gabriel Rossetti', '1861', 'The sonnets and canzoni for Beatrice with Dante\'s own prose commentary: how a boy of nine fell in love and what he made of it.', None, None),
    ('virgil-georgics', 232, 'The Georgics', 'Virgil', (-70, -19), 'la', -29, 'James Rhoades', '1881', 'Four books on farming that are really about labour, loss and the Orpheus who looked back.', 'blank verse', None),
    ('lucan-pharsalia', 602, 'Pharsalia', 'Lucan', (39, 65), 'la', 61, 'Edward Ridley', '1896', 'The civil war between Caesar and Pompey, told without gods: the anti-Aeneid, and Erichtho\'s necromancy in Book VI.', 'blank verse', None),
    ('petrarch-sonnets', 17650, 'The Sonnets, Triumphs and Other Poems', 'Petrarch', (1304, 1374), 'it', 1350, 'various hands', '1859', 'The sonnets to Laura that gave Europe the love sonnet, in the Bohn versions by Macgregor, Nott, Wrottesley and others.', None, 'ABBAABBACDCDCD'),
    ('lay-of-the-cid', 6088, 'The Lay of the Cid', 'Anonymous (Old Spanish)', (None, None), 'es', 1200, 'R. Selden Rose and Leonard Bacon', '1919', 'Spain\'s national epic: the exile, the campaigns and the honour of Rodrigo Díaz de Vivar.', None, None),
    ('michelangelo-sonnets', 10314, 'Sonnets', 'Michelangelo Buonarroti', (1475, 1564), 'it', 1540, 'John Addington Symonds', '1878', 'The sculptor\'s sonnets to Vittoria Colonna and Tommaso Cavalieri, on love, age and the stone.', None, None),
    ('garcilaso-works', 49410, 'The Works of Garcilasso de la Vega', 'Garcilaso de la Vega', (1503, 1536), 'es', 1535, 'J. H. Wiffen', '1823', 'The soldier-poet who brought the Italian line into Spanish and died at thirty-three.', None, None),
    ('leopardi-poems', 53020, 'The Poems of Leopardi', 'Giacomo Leopardi', (1798, 1837), 'it', 1830, 'Frederick Townsend', '1887', 'The greatest Italian poet after Dante: the infinite, the broom on Vesuvius, and a clear-eyed despair.', None, None),
    ('heine-poems-ballads', 31726, 'Poems and Ballads', 'Heinrich Heine', (1797, 1856), 'de', 1830, 'Emma Lazarus', '1881', 'The Lorelei, the Book of Songs and the late poems from the mattress-grave, translated by Emma Lazarus.', None, None),
    ('verlaine-poems', 8426, 'Poems', 'Paul Verlaine', (1844, 1896), 'fr', 1875, 'Gertrude Hall', '1895', 'Music before everything else: the Fêtes galantes and the Romances sans paroles.', None, None),
    ('mickiewicz-crimea', 27069, 'Sonnets from the Crimea', 'Adam Mickiewicz', (1798, 1855), 'pl', 1826, 'Edna Worthley Underwood', '1917', 'Poland\'s national poet in exile, looking at the Crimean steppe and mountains.', None, None),
    ('waley-chinese', 42290, 'A Hundred and Seventy Chinese Poems', 'Various (Chinese)', (None, None), 'zh', 800, 'Arthur Waley', '1918', 'Po Chü-i and the Chinese tradition in the versions that changed English poetry: Pound, Eliot and the Imagists all read them.', 'free verse', None),
    ('lute-of-jade', 390, 'A Lute of Jade', 'Various (Chinese)', (None, None), 'zh', 750, 'L. Cranmer-Byng', '1909', 'Li Po, Tu Fu and the classical Chinese poets, in the Wisdom of the East series.', None, None),
    ('kalidasa-shakuntala', 16659, 'Shakuntala and Other Works', 'Kalidasa', (None, None), 'sa', 400, 'Arthur W. Ryder', '1912', 'India\'s greatest classical poet: the play of the lost ring, and the Cloud Messenger.', None, None),
    ('hafiz-divan', 74883, 'Poems from the Divan of Hafiz', 'Hafiz', (None, None), 'fa', 1370, 'Gertrude Lowthian Bell', '1897', 'The wine, the rose and the nightingale of Shiraz, in Gertrude Bell\'s versions.', None, None),
    ('poetic-edda', 73533, 'The Poetic Edda', 'Anonymous (Old Norse)', (None, None), 'non', 1000, 'Henry Adams Bellows', '1923', 'The Norse mythological and heroic lays, from the Völuspá to the Lay of Hamther.', None, None),
    ('mahabharata', 19630, 'The Mahabharata (condensed)', 'Vyasa (traditional)', (None, None), 'sa', -400, 'Romesh Chunder Dutt', '1899', 'The war of the Kurus and Pandavas, condensed into English verse.', None, None),
    ('rubaiyat', 246, 'The Rubaiyat of Omar Khayyam', 'Omar Khayyam', (1048, 1131), 'fa', 1120, 'Edward FitzGerald', '1859', 'FitzGerald\'s quatrains, more his own poem than a translation, and one of the most quoted in English.', None, 'AABA'),
    ('faerie-queene', 15272, 'The Faerie Queene, Book I', 'Edmund Spenser', (1552, 1599), 'en', 1590, None, '1590', 'The Legend of the Knight of the Red Cross, the first book of Spenser\'s allegorical epic, in the nine-line stanza named after him.', None, 'ABABBCBCC'),
    ('paradise-regained', 58, 'Paradise Regained', 'John Milton', (1608, 1674), 'en', 1671, None, '1671', 'Christ\'s temptation in the wilderness, in four books of blank verse.', 'blank verse', None),
    ('canterbury-tales', 2383, 'The Canterbury Tales', 'Geoffrey Chaucer', (1343, 1400), 'enm', 1400, None, '1400', 'The pilgrims\' tales in Middle English with modernised spelling (Purves edition), so the dictionary readings are approximate.', None, None),
]

# Original-language texts shown beside the translations in the reader (reader only; not analysed or quizzed).
# (translation slug, gutenberg id, language, source label, heading regex used to keep only the poem's numbered sections)
# manuscript sigla and rubric labels: two or more on a line means a collation note, not verse
APPARATUS = re.compile(r'^\s*(HEADING|COLOPHON|RUBRIC|INCIPIT|EXPLICIT)\b'
                       r'|(?:\b(?:Hl|Pt|Ln|Cm|Cp|Hn|Ha|Dd|Sl|Gg|Ld|Seld|Reg|Harl|Camb|Corp|Petw|Lans)\.\s[^;]{0,40}[;.]\s*){2,}')
ORIGINALS = [
    ('canterbury-tales', 22120, 'enm', 'The Canterbury Tales in Middle English, Skeat\'s text (Project Gutenberg #22120)', None),  # SLUG_META start_at skips Skeat's preface
    ('virgil-aeneid', 227, 'la', 'Aeneidos, Latin text (Project Gutenberg #227)', r'liber'),
    ('dante-divine-comedy', 1012, 'it', 'La Divina Commedia, Italian text (Project Gutenberg #1012)', r'canto'),
    ('orlando-furioso', 3747, 'it', 'Orlando Furioso, Italian text (Project Gutenberg #3747)', r'canto'),
    ('lusiads', 3333, 'pt', 'Os Lusíadas, Portuguese text (Project Gutenberg #3333)', r'canto'),
    ('goethe-faust', 2229, 'de', 'Faust, der Tragödie erster Teil, German text (Project Gutenberg #2229)', None),
    ('kalevala', 7000, 'fi', 'Kalevala, Finnish text (Project Gutenberg #7000)', r'runo'),
    ('nibelungenlied', 14915, 'de', 'Das Nibelungenlied, Middle High German text (Project Gutenberg #14915)', r'ventiure|abenteuer'),
    ('beowulf', 9701, 'ang', 'Beowulf, Old English text, Harrison and Sharp edition of 1883 (Project Gutenberg #9701)', r'^(Fitt|Part|Prelude)\b'),
]

def resolve(query, rows):
    if isinstance(query, int): return next((r for r in rows if r['Text#'] == str(query)), None)
    if '|' in query:
        a, t = [x.strip().lower() for x in query.split('|', 1)]
        hits = [r for r in rows if a in r['Authors'].lower().split(';')[0] and all(x in r['Title'].lower() for x in t.split())]
    else:
        q = query.lower().split()
        hits = [r for r in rows if all(x in (r['Title'] + ' ' + r['Authors']).lower() for x in q)]
    # prefer shorter titles (single works over "complete works") and earlier ids
    hits.sort(key=lambda r: (len(r['Title']), int(r['Text#'])))
    return hits[0] if hits else None

NAME_FIX = {'Brontë, Charlotte': 'Charlotte, Emily and Anne Brontë', 'Meynell, Alice Christiana Thompson': 'Alice Meynell', 'Benét, Stephen Vincent': 'Stephen Vincent Benét', 'De la Mare, Walter': 'Walter de la Mare', 'Henley, William Ernest': 'W. E. Henley', 'Johnson, Lionel Pigot': 'Lionel Johnson', 'Freneau, Philip Morin': 'Philip Freneau', 'Landor, Walter Savage': 'Walter Savage Landor', 'Chesterton, G. K. (Gilbert Keith)': 'G. K. Chesterton', 'Dowson, Ernest Christopher': 'Ernest Dowson', 'Mew, Charlotte Mary': 'Charlotte Mew', 'Crow, Martha Foote': 'Samuel Daniel', 'Williams, William Carlos': 'William Carlos Williams', 'Crane, Hart': 'Hart Crane', 'Byron': 'Lord Byron', 'Byron, George Gordon Byron': 'Lord Byron', 'Hemans': 'Felicia Hemans', 'Hemans, Mrs.': 'Felicia Hemans', 'Rossetti, Christina Georgina': 'Christina Rossetti', 'H. D.': 'H.D.', 'Doolittle, Hilda': 'H.D.', 'Tennyson, Alfred Tennyson': 'Alfred Tennyson', 'Yeats, W. B.': 'W. B. Yeats', 'Eliot, T. S.': 'T. S. Eliot', 'Housman, A. E.': 'A. E. Housman', 'Lawrence, D. H.': 'D. H. Lawrence', 'Service, Robert W.': 'Robert W. Service', 'Wordsworth, William': 'William Wordsworth'}

# Where NAME_FIX replaces one person with another — Gutenberg files Daniel's Delia under its editor,
# Martha Foote Crow — the dates in the Authors field are the wrong person's and have to be replaced too.
# Hughes and McKay are a different case: the catalogue carries the birth years the poets themselves gave
# out (Hughes 1902, McKay 1890) and the registers have since settled it the other way, Hughes born
# 1 February 1901 and McKay 15 September 1889. pipeline/dates.py applies the same corrections to the
# data already on disk, so the two do not have to agree by accident.
# Langland is a third case: the catalogue's 1330?-1400? is the older guess, the references settle on
# c. 1332 to c. 1386, and the site was corrected to those by hand in September 2026 without the
# index being told, so a re-parse would have put 1330-1400 back.
# Lovelace and Traherne are the same story as Langland: corrected on the site by hand, never in the
# index, so the next analyze.py would have printed 1618-1658 and no dates at all for Traherne again.
DATE_FIX = {'Samuel Daniel': (1562, 1619), 'Langston Hughes': (1901, 1967), 'Claude McKay': (1889, 1948),
            'William Langland': (1332, 1386), 'Richard Lovelace': (1617, 1657), 'Thomas Traherne': (1636, 1674)}

# Poets whose year is a scholarly guess, and which of the two: 'b', 'd' or 'bd'. Eleven of them are
# taken from the question marks in the Authors field of the Gutenberg catalogue (the only poets in this
# library it marks), Langland from the same convention every reference follows, c. 1332 to c. 1386;
# his dates were set by hand here and the catalogue's entry for Piers Plowman does not carry them.
# The works in EPICS and ORIGINALS below have their dates written by hand too, which is why this is
# keyed by poet rather than read from the catalogue at the point of use.
CIRCA = {'Geoffrey Chaucer': 'b', 'John Gower': 'b', 'John Skelton': 'b', 'Edmund Spenser': 'b',
         'Sir Walter Raleigh': 'b', 'Ben Jonson': 'b', 'Richard Crashaw': 'b', 'Nicholas Breton': 'd',
         'Oliver Goldsmith': 'b', 'Luís de Camões': 'b', 'Ebenezer Cooke': 'bd', 'William Langland': 'bd'}

def author_meta(authors):
    """Display name, sort name, born, died, and which of the two dates the catalogue marks uncertain.

    The Authors field writes an uncertain year with a question mark, "Chaucer, Geoffrey, 1343?-1400".
    That mark was read and thrown away, so the site printed a guess as a fact. It is kept now as
    'b', 'd' or 'bd' and comes out as "c. 1343" where the years are shown.
    """
    first = authors.split(';')[0].strip()
    m = re.match(r'^(.*?),\s*(\d{4})(\?)?-(\d{4})?(\?)?', first)
    name_sort = re.sub(r',\s*\d{4}.*$', '', first)
    name_sort = re.sub(r'\s*\(.*?\)', '', name_sort)
    parts = [p.strip() for p in name_sort.split(',')]
    display = (parts[1] + ' ' + parts[0]) if len(parts) > 1 else parts[0]
    if len(parts) > 1 and parts[1].endswith(parts[0]): display = parts[1]
    display = NAME_FIX.get(parts[0] + (', ' + parts[1] if len(parts) > 1 else ''), NAME_FIX.get(parts[0], display))
    born = int(m.group(2)) if m else None; died = int(m.group(4)) if m and m.group(4) else None
    circa = ('b' if m and m.group(3) else '') + ('d' if m and m.group(5) else '')
    if display in DATE_FIX: born, died = DATE_FIX[display]; circa = ''
    return display, name_sort, born, died, CIRCA.get(display, circa)

def fetch(gid):
    path = os.path.join(SRC, f'pg{gid}.txt')
    if os.path.exists(path): return path
    for url in (f'https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt', f'https://www.gutenberg.org/files/{gid}/{gid}-0.txt', f'https://www.gutenberg.org/files/{gid}/{gid}.txt'):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read()
            if b'*** START OF' in data: open(path, 'wb').write(data); return path
        except Exception as e: pass
    return None

def mark_prose(w, meta):
    """Flag the sections an edition prints as prose -- FitzGerald's introduction to the Rubaiyat, Wheatley's
    preface, Dowson's story -- so that nothing downstream letters them for rhyme, scans them or names a
    metre. They stay in the book, because they are part of it; they are marked for what they are. The
    parser drops most prose by its shape; these survived because a wrapped line can start with a capital."""
    pat = meta.get('prose_re')
    if not pat: return w
    for s in w['sections']:
        if re.match(pat, s['title'], re.I): s['prose'] = True
    return w

if __name__ == '__main__':
    rows = [r for r in csv.DictReader(open(CAT, encoding='utf-8')) if r['Language'] == 'en' and r['Type'] == 'Text']
    index = json.load(open(os.path.join(OUT, 'index.json')))
    only = set(a for a in sys.argv[1:] if not a.startswith('-'))
    keep = [w for w in index if w['slug'] in ('don-juan', 'shakespeare-sonnets', 'the-raven', 'ancient-mariner', 'keats-1820', 'tennyson-in-memoriam') or (only and w['slug'] not in only)]
    report = []
    for slug, query, title, blurb, published, hint in QUERIES:
        if only and slug not in only: continue
        r = resolve(query, rows)
        if not r: report.append((slug, 'NOT FOUND', query)); continue
        gid = int(r['Text#']); path = fetch(gid)
        if not path: report.append((slug, 'NO TEXT', gid)); continue
        author, author_sort, born, died, circa = author_meta(r['Authors'])
        meta = {'title': title, 'title_as_published': r['Title'], 'author': author, 'author_sort': author_sort, 'born': born, 'died': died, 'circa': circa, 'published': published, 'blurb': blurb,
                'form': None, 'scheme': {'sonnet': 'ABABCDCDEFEFGG', 'petrarchan': 'ABBAABBACDCDCD', 'spenserian': 'ABABBCBCC'}.get(hint), 'meter': hint if hint in ('blank verse', 'heroic couplets', 'free verse', 'trochaic tetrameter', 'dactylic hexameter') else None}
        meta.update(SLUG_META.get(slug, {}))
        try:
            w = parse_gutenberg(gid, slug, meta)
        except Exception as e:
            report.append((slug, 'PARSE ERROR', str(e)[:80])); continue
        w = mark_prose(w, meta)
        nl = sum(len(st) for s in w['sections'] for st in s['stanzas'])
        if nl < 60 or not w['sections']:
            report.append((slug, 'TOO LITTLE', f'{gid} {r["Title"][:40]} lines={nl}')); continue
        if not w['meter']:
            _lab, _sh = meter_share(w)
            w['meter'] = _lab or 'mixed'; w['meter_conf'] = round(_sh, 3)
        else: w['meter_conf'] = 1.0
        # `meter` stays as the working hint analyze.py and measures.py read for a syllable target; the FORM
        # is what a page prints as a claim, and below METER_FLOOR the claim is not made (Hopkins was
        # "Mostly iambic pentameter" on 18% of his lines).
        if not w['form']: w['form'] = {'blank verse': 'Blank verse: unrhymed iambic pentameter', 'heroic couplets': 'Heroic couplets: rhymed pairs of iambic pentameter', 'free verse': 'Free verse', 'iambic pentameter': 'Mostly iambic pentameter', 'iambic tetrameter': 'Mostly iambic tetrameter'}.get(w['meter'] if w['meter_conf'] >= METER_FLOOR else None, 'Mixed forms')
        w['stats'] = {'sections': len(w['sections']), 'stanzas': sum(len(s['stanzas']) for s in w['sections']), 'lines': nl}
        w = apply_corrections(w)
        json.dump(w, open(os.path.join(OUT, slug + '.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
        keep.append({k: w[k] for k in ('slug', 'title', 'author', 'author_sort', 'born', 'died', 'circa', 'published', 'form', 'scheme', 'meter', 'meter_conf', 'blurb', 'stats')})
        report.append((slug, 'OK', f'{gid} {r["Title"][:38]} | {author} | poems={len(w["sections"])} lines={nl}'))
    for slug, gid, title, orig, dates, lang, composed, translator, tyear, blurb, hint, scheme in EPICS:
        if only and slug not in only: continue
        path = fetch(gid)
        for g in SLUG_META.get(slug, {}).get('append_gids', []): fetch(g)
        if not path: report.append((slug, 'NO TEXT', gid)); continue
        _nm = orig.split(' (')[0].split(' ')
        sort_name = title if orig.startswith('Anonymous') else (_nm[-1] + ', ' + ' '.join(_nm[:-1])).strip(', ')
        meta = {'title': title, 'title_as_published': title, 'author': orig, 'author_sort': sort_name, 'born': dates[0], 'died': dates[1], 'circa': CIRCA.get(orig, ''), 'published': tyear, 'blurb': blurb,
                'lang': lang, 'original_title': title, 'composed': composed, 'translator': translator, 'epic': True, 'max_lines': 20000, 'longs': slug == 'faerie-queene',
                'form': None, 'scheme': scheme, 'meter': hint}
        # roman numerals under a prose heading are the manuscript's fitts, not parts of the heading
        if slug == 'goethe-faust': meta['titlere'] = r"^(DEDICATION|PRELUDE AT THE THEATRE|PROLOGUE IN HEAVEN|NIGHT|BEFORE THE CITY-GATE|THE STUDY|AUERBACH.S CELLAR IN LEIPZIG|WITCHES. KITCHEN|A STREET|STREET|EVENING A SMALL, NEATLY KEPT CHAMBER|PROMENADE|THE NEIGHBOR.S HOUSE|GARDEN|A GARDEN-ARBOR|FOREST AND CAVERN|MARGARET.S ROOM|MARTHA.S GARDEN|AT THE FOUNTAIN|DONJON|CATHEDRAL|WALPURGIS-NIGHT|OBERON AND TITANIA.S GOLDEN WEDDING|DREARY DAY|DUNGEON)$"
        if slug == 'canterbury-tales': meta['inline_gloss'] = "Glosses from the Purves edition of 1870, printed beside the lines (Project Gutenberg #2383)."
        meta.update(SLUG_META.get(slug, {}))
        try: w = parse_gutenberg(gid, slug, meta)
        except Exception as e: report.append((slug, 'PARSE ERROR', str(e)[:80])); continue
        w = mark_prose(w, meta)
        nl = sum(len(st) for s in w['sections'] for st in s['stanzas'])
        if nl < 200: report.append((slug, 'TOO LITTLE', f'{gid} lines={nl}')); continue
        if not w['meter']:
            _lab, _sh = meter_share(w)
            w['meter'] = _lab or 'mixed'; w['meter_conf'] = round(_sh, 3)
        else: w['meter_conf'] = 1.0
        if not w['form']: w['form'] = {'blank verse': 'Blank verse: unrhymed iambic pentameter', 'heroic couplets': 'Heroic couplets: rhymed pairs of iambic pentameter', 'trochaic tetrameter': 'Trochaic tetrameter', 'alliterative verse': 'Alliterative four-stress verse', 'iambic pentameter': 'Mostly iambic pentameter', 'iambic tetrameter': 'Mostly iambic tetrameter'}.get(w['meter'] if w['meter_conf'] >= METER_FLOOR else None, 'Mixed forms')
        w['stats'] = {'sections': len(w['sections']), 'stanzas': sum(len(s['stanzas']) for s in w['sections']), 'lines': nl}
        w = apply_corrections(w)
        if w.get('orig_sections'):
            json.dump({'lang': lang, 'source': f'{orig}, {title}: original text printed with the {translator} translation (Project Gutenberg #{gid})', 'multi': False, 'sections': w.pop('orig_sections')}, open(os.path.join(OUT, slug + '.orig.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
        json.dump(w, open(os.path.join(OUT, slug + '.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
        keep.append({k: w.get(k) for k in ('slug', 'title', 'author', 'author_sort', 'born', 'died', 'circa', 'published', 'form', 'scheme', 'meter', 'meter_conf', 'blurb', 'stats', 'lang', 'original_title', 'composed', 'translator', 'epic')})
        report.append((slug, 'OK', f'{gid} | {orig} tr. {translator} | sections={len(w["sections"])} lines={nl}'))
    for slug, gid, lang, label, headre in ORIGINALS:
        path = fetch(gid)
        if not path: report.append((slug + ' (orig)', 'NO TEXT', gid)); continue
        ometa = {'title': label, 'author': '', 'epic': True, 'max_lines': 60000, 'lang': lang, 'headre': headre}; ometa.update(SLUG_META.get(slug + '-orig', {}))
        try: w = parse_gutenberg(gid, slug + '-orig', ometa, min_lines=2)
        except Exception as e: report.append((slug + ' (orig)', 'PARSE ERROR', str(e)[:80])); continue
        secs = w['sections']
        if headre: secs = [x for x in secs if re.search(headre, x['title'], re.I)] or secs
        if slug == 'beowulf':
            # Harrison and Sharp number the prelude as fitt I; Gummere's translation calls it the Prelude and counts from the hall
            def shift(t):
                m = re.match(r'^Fitt ([IVXL]+)(.*)$', t)
                if not m: return t
                n = generic.roman_to_int(m.group(1)) - 1
                return ('Prelude' if n == 0 else 'Part ' + generic.to_roman(n)) + m.group(2)
            for x in secs: x['title'] = shift(x['title'])
        # An old scholarly edition prints its collation of the manuscripts in the same measure as the verse.
        # Skeat's Chaucer does it after every few hundred lines. Those lines are apparatus, not the poem.
        dropped = 0
        for x in secs:
            kept = []
            for st in x['stanzas']:
                ln = [l for l in st if not APPARATUS.search(l)]
                dropped += len(st) - len(ln)
                if ln: kept.append(ln)
            x['stanzas'] = kept
        secs = [x for x in secs if not x['title'].lstrip().startswith(('§', 'Note ')) and sum(len(st) for st in x['stanzas']) >= 4]
        nl = sum(len(st) for x in secs for st in x['stanzas'])
        json.dump({'lang': lang, 'source': label, 'multi': any(':' in x['title'] for x in secs), 'sections': secs}, open(os.path.join(OUT, slug + '.orig.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
        report.append((slug + ' (orig)', 'OK', f'{gid} {lang} sections={len(secs)} lines={nl}'))
    json.dump(keep, open(os.path.join(OUT, 'index.json'), 'w'), ensure_ascii=False, indent=1)
    for r in report: print(f'{r[0]:28s} {r[1]:12s} {r[2]}')
    print('works in index:', len(keep))
